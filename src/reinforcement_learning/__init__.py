"""
Reinforcement Learning Module for Adaptive Face Recognition

This module implements Human-in-the-Loop (HITL) reinforcement learning
to adaptively improve recognition accuracy over time through user feedback.
"""

from .hitl_trainer import ReinforcementTracker

__all__ = ['ReinforcementTracker']
