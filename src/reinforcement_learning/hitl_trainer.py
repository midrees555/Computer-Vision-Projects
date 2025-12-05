"""
Human-in-the-Loop (HITL) Reinforcement Learning Tracker

This module implements an adaptive learning system that:
1. Tracks predictions and their confidence scores
2. Accepts user feedback (rewards/penalties)
3. Dynamically adjusts recognition thresholds
4. Maintains per-person accuracy statistics
5. Persists learning across sessions

Industry Use Cases:
- Facebook Face Tagging: "Is this you?" feedback
- Google Photos: Face clustering correction
- Security Systems: False positive/negative adjustment
"""

import numpy as np
from datetime import datetime, timedelta
import pickle
import os
from collections import defaultdict
import json


class ReinforcementTracker:
    """
    Adaptive threshold tracker using reinforcement learning principles.
    
    Key Features:
    - Global threshold adaptation (increases for false positives, decreases for false negatives)
    - Per-person threshold customization based on individual accuracy
    - Exponential moving average for smooth threshold updates
    - Confidence calibration over time
    - Persistent state across sessions
    """
    
    def __init__(self, 
                 learning_rate=0.02,
                 threshold_bounds=(0.65, 0.92),
                 initial_threshold=0.80,
                 max_pending=100):
        """
        Initialize the reinforcement tracker.
        
        Args:
            learning_rate (float): Speed of threshold adaptation (0.01-0.05 recommended)
            threshold_bounds (tuple): (min, max) threshold limits
            initial_threshold (float): Starting similarity threshold
            max_pending (int): Maximum number of predictions to keep for feedback
        """
        self.learning_rate = learning_rate
        self.min_threshold, self.max_threshold = threshold_bounds
        self.threshold = initial_threshold
        
        # Prediction tracking for feedback
        self.pending_feedback = []  # Recent predictions awaiting feedback
        self.max_pending = max_pending
        
        # Learning history
        self.feedback_history = []  # All feedback received
        
        # Per-person adaptive thresholds and statistics
        self.person_thresholds = {}  # {person_name: adaptive_threshold}
        self.person_stats = defaultdict(lambda: {
            'correct': 0,
            'incorrect': 0,
            'total': 0,
            'avg_similarity': 0.0,
            'confidence_sum': 0.0
        })
        
        # Confidence calibration
        self.similarity_correct = []  # Similarities for correct predictions
        self.similarity_incorrect = []  # Similarities for incorrect predictions
        
        # Session statistics
        self.session_start = datetime.now()
        self.session_feedback_count = 0
        
    def log_prediction(self, embedding, predicted_name, similarity, frame_id, timestamp=None):
        """
        Log a prediction for potential feedback.
        
        Args:
            embedding (np.ndarray): Face embedding vector (128-d)
            predicted_name (str): Predicted person name or "Unknown"
            similarity (float): Cosine similarity score
            frame_id (int): Frame/detection identifier
            timestamp (datetime): Optional timestamp (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        prediction = {
            'embedding': embedding.copy() if isinstance(embedding, np.ndarray) else embedding,
            'predicted': predicted_name,
            'similarity': similarity,
            'frame_id': frame_id,
            'timestamp': timestamp
        }
        
        self.pending_feedback.append(prediction)
        
        # Limit size to prevent memory issues
        if len(self.pending_feedback) > self.max_pending:
            self.pending_feedback.pop(0)
    
    def provide_feedback(self, frame_id, is_correct, true_name=None):
        """
        Provide feedback on a prediction (reward or penalty).
        
        This is the core RL update step:
        - Reward (+1): Prediction was correct → relax threshold (more lenient)
        - Penalty (-1): Prediction was wrong → tighten threshold (more strict)
        
        Args:
            frame_id (int): Frame identifier to provide feedback on
            is_correct (bool): True if prediction was correct
            true_name (str): Ground truth name (required if is_correct=False)
        
        Returns:
            dict: Feedback result with reward, old/new thresholds, and statistics
        """
        # Find the prediction
        pred = next((p for p in self.pending_feedback if p['frame_id'] == frame_id), None)
        if not pred:
            return {
                'success': False,
                'message': f"Frame {frame_id} not found in pending feedback"
            }
        
        # Calculate reward
        reward = 1.0 if is_correct else -1.0
        predicted_name = pred['predicted']
        similarity = pred['similarity']
        
        # Determine the actual person's name
        actual_name = predicted_name if is_correct else (true_name or "Unknown")
        
        # Update global threshold using gradient-based adaptation
        old_threshold = self.threshold
        if is_correct:
            # Correct prediction: slightly lower threshold (be more lenient)
            # But only if similarity was close to threshold (avoid over-relaxing)
            if similarity < self.threshold + 0.1:
                adjustment = -self.learning_rate * (self.threshold - similarity)
                self.threshold = max(self.min_threshold, self.threshold + adjustment)
        else:
            # Incorrect prediction: increase threshold (be more strict)
            # Larger adjustment if similarity was high (false positive is worse)
            adjustment = self.learning_rate * (1.0 + similarity)
            self.threshold = min(self.max_threshold, self.threshold + adjustment)
        
        # Update per-person statistics
        stats = self.person_stats[actual_name]
        stats['total'] += 1
        stats['confidence_sum'] += similarity
        stats['avg_similarity'] = stats['confidence_sum'] / stats['total']
        
        if is_correct:
            stats['correct'] += 1
            self.similarity_correct.append(similarity)
        else:
            stats['incorrect'] += 1
            self.similarity_incorrect.append(similarity)
        
        # Adaptive per-person threshold
        accuracy = stats['correct'] / stats['total'] if stats['total'] > 0 else 0
        
        if stats['total'] >= 5:  # Need minimum samples for reliable adaptation
            if accuracy < 0.75:
                # Low accuracy → increase person's threshold (be more strict)
                self.person_thresholds[actual_name] = min(
                    self.max_threshold,
                    self.threshold + 0.08
                )
            elif accuracy > 0.95 and stats['total'] >= 10:
                # High accuracy with good sample size → relax threshold
                self.person_thresholds[actual_name] = max(
                    self.min_threshold,
                    self.threshold - 0.05
                )
            else:
                # Moderate accuracy → use global threshold
                if actual_name in self.person_thresholds:
                    # Gradually converge to global threshold
                    self.person_thresholds[actual_name] = (
                        0.7 * self.person_thresholds[actual_name] +
                        0.3 * self.threshold
                    )
        
        # Log feedback
        feedback_entry = {
            'timestamp': datetime.now(),
            'frame_id': frame_id,
            'predicted': predicted_name,
            'actual': actual_name,
            'is_correct': is_correct,
            'similarity': similarity,
            'reward': reward,
            'old_threshold': old_threshold,
            'new_threshold': self.threshold
        }
        self.feedback_history.append(feedback_entry)
        self.session_feedback_count += 1
        
        # Remove from pending
        self.pending_feedback = [p for p in self.pending_feedback if p['frame_id'] != frame_id]
        
        # Return detailed feedback result
        return {
            'success': True,
            'reward': reward,
            'old_threshold': old_threshold,
            'new_threshold': self.threshold,
            'predicted': predicted_name,
            'actual': actual_name,
            'similarity': similarity,
            'person_accuracy': accuracy,
            'message': f"{'✓ Correct' if is_correct else '✗ Wrong'} | "
                      f"Similarity: {similarity:.3f} | "
                      f"Threshold: {old_threshold:.3f} → {self.threshold:.3f}"
        }
    
    def provide_feedback_on_latest(self, is_correct, true_name=None):
        """
        Provide feedback on the most recent prediction.
        
        Convenience method for quick feedback without tracking frame IDs.
        
        Args:
            is_correct (bool): True if prediction was correct
            true_name (str): Ground truth name (if incorrect)
        
        Returns:
            dict: Feedback result
        """
        if not self.pending_feedback:
            return {
                'success': False,
                'message': "No pending predictions to provide feedback on"
            }
        
        latest = self.pending_feedback[-1]
        return self.provide_feedback(latest['frame_id'], is_correct, true_name)
    
    def get_threshold(self, person_name=None):
        """
        Get the adaptive threshold for recognition.
        
        Args:
            person_name (str): Person to get threshold for (None = global)
        
        Returns:
            float: Adaptive threshold value
        """
        if person_name and person_name in self.person_thresholds:
            return self.person_thresholds[person_name]
        return self.threshold
    
    def get_statistics(self):
        """
        Get comprehensive learning statistics.
        
        Returns:
            dict: Statistics including accuracy, thresholds, and per-person metrics
        """
        # Recent feedback analysis (last 20)
        recent_feedback = self.feedback_history[-20:]
        recent_correct = sum(1 for f in recent_feedback if f['is_correct'])
        recent_accuracy = recent_correct / len(recent_feedback) if recent_feedback else 0
        
        # Overall accuracy
        total_feedback = len(self.feedback_history)
        overall_correct = sum(1 for f in self.feedback_history if f['is_correct'])
        overall_accuracy = overall_correct / total_feedback if total_feedback > 0 else 0
        
        # Confidence calibration
        avg_similarity_correct = (
            np.mean(self.similarity_correct) if self.similarity_correct else 0
        )
        avg_similarity_incorrect = (
            np.mean(self.similarity_incorrect) if self.similarity_incorrect else 0
        )
        
        # Per-person statistics (top 10 by total interactions)
        person_stats_list = [
            {
                'name': name,
                'accuracy': stats['correct'] / stats['total'] if stats['total'] > 0 else 0,
                'total': stats['total'],
                'correct': stats['correct'],
                'incorrect': stats['incorrect'],
                'avg_similarity': stats['avg_similarity'],
                'custom_threshold': self.person_thresholds.get(name, None)
            }
            for name, stats in self.person_stats.items()
        ]
        person_stats_list.sort(key=lambda x: x['total'], reverse=True)
        
        # Session duration
        session_duration = datetime.now() - self.session_start
        
        return {
            'global_threshold': self.threshold,
            'threshold_bounds': [self.min_threshold, self.max_threshold],
            'recent_accuracy': recent_accuracy,
            'overall_accuracy': overall_accuracy,
            'total_feedback': total_feedback,
            'session_feedback': self.session_feedback_count,
            'session_duration_minutes': session_duration.total_seconds() / 60,
            'pending_predictions': len(self.pending_feedback),
            'confidence_calibration': {
                'avg_similarity_correct': float(avg_similarity_correct),
                'avg_similarity_incorrect': float(avg_similarity_incorrect),
                'separation': float(avg_similarity_correct - avg_similarity_incorrect)
            },
            'person_stats': person_stats_list[:10],  # Top 10
            'persons_with_custom_thresholds': len(self.person_thresholds)
        }
    
    def get_pending_predictions(self, limit=10):
        """
        Get recent predictions awaiting feedback.
        
        Args:
            limit (int): Maximum number to return
        
        Returns:
            list: Recent predictions
        """
        return [
            {
                'frame_id': p['frame_id'],
                'predicted': p['predicted'],
                'similarity': p['similarity'],
                'timestamp': p['timestamp'].strftime('%H:%M:%S')
            }
            for p in self.pending_feedback[-limit:]
        ]
    
    def save(self, path='data/rl_tracker.pkl'):
        """
        Save the learning state to disk for persistence.
        
        Args:
            path (str): File path to save to
        """
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        save_data = {
            'threshold': self.threshold,
            'person_thresholds': self.person_thresholds,
            'person_stats': dict(self.person_stats),
            'feedback_history': self.feedback_history,
            'similarity_correct': self.similarity_correct,
            'similarity_incorrect': self.similarity_incorrect,
            'learning_rate': self.learning_rate,
            'threshold_bounds': (self.min_threshold, self.max_threshold),
            'version': '1.0.0',
            'last_saved': datetime.now().isoformat()
        }
        
        with open(path, 'wb') as f:
            pickle.dump(save_data, f, protocol=pickle.HIGHEST_PROTOCOL)
        
        print(f"✓ RL: Saved learning state to {path}")
        print(f"  - Global threshold: {self.threshold:.3f}")
        print(f"  - Total feedback: {len(self.feedback_history)}")
        print(f"  - Persons tracked: {len(self.person_stats)}")
    
    def load(self, path='data/rl_tracker.pkl'):
        """
        Load previous learning state from disk.
        
        Args:
            path (str): File path to load from
        
        Returns:
            bool: True if loaded successfully, False otherwise
        """
        if not os.path.exists(path):
            print(f"ℹ RL: No previous learning state found at {path}")
            return False
        
        try:
            with open(path, 'rb') as f:
                data = pickle.load(f)
            
            # Restore state
            self.threshold = data['threshold']
            self.person_thresholds = data['person_thresholds']
            self.person_stats = defaultdict(lambda: {
                'correct': 0, 'incorrect': 0, 'total': 0,
                'avg_similarity': 0.0, 'confidence_sum': 0.0
            })
            self.person_stats.update(data['person_stats'])
            self.feedback_history = data['feedback_history']
            self.similarity_correct = data.get('similarity_correct', [])
            self.similarity_incorrect = data.get('similarity_incorrect', [])
            
            # Update learning parameters if saved
            if 'learning_rate' in data:
                self.learning_rate = data['learning_rate']
            if 'threshold_bounds' in data:
                self.min_threshold, self.max_threshold = data['threshold_bounds']
            
            last_saved = data.get('last_saved', 'Unknown')
            print(f"✓ RL: Loaded learning state from {path}")
            print(f"  - Global threshold: {self.threshold:.3f}")
            print(f"  - Total feedback: {len(self.feedback_history)}")
            print(f"  - Persons tracked: {len(self.person_stats)}")
            print(f"  - Last saved: {last_saved}")
            
            return True
            
        except Exception as e:
            print(f"✗ RL: Failed to load learning state: {e}")
            return False
    
    def export_statistics_json(self, path='data/rl_statistics.json'):
        """
        Export statistics to JSON for external analysis.
        
        Args:
            path (str): File path to export to
        """
        stats = self.get_statistics()
        
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump(stats, f, indent=2, default=str)
        
        print(f"✓ Exported RL statistics to {path}")
    
    def reset(self):
        """Reset all learning state (use with caution)."""
        self.threshold = 0.80
        self.person_thresholds = {}
        self.person_stats = defaultdict(lambda: {
            'correct': 0, 'incorrect': 0, 'total': 0,
            'avg_similarity': 0.0, 'confidence_sum': 0.0
        })
        self.feedback_history = []
        self.similarity_correct = []
        self.similarity_incorrect = []
        self.pending_feedback = []
        self.session_start = datetime.now()
        self.session_feedback_count = 0
        print("⚠ RL: All learning state has been reset")
