# ===================================================================
#  PowerShell Script to Launch the Face Recognition Security System
# ===================================================================

# Set the title of the PowerShell window for a professional look.
$Host.UI.RawUI.WindowTitle = "Face Recognition Security System Launcher"

# --- IMPORTANT ---
# Define the absolute path to your project's root directory.
# This ensures that all relative paths inside the Python code (like 'src/', 'models/') work correctly.
$projectPath = "d:\00_Data_Root\02_Master_Data_Repository\02_Courses_&_Skills\02_NAVTTC_Courses\Main_Course_Work\11_Project\Face_Recognition"

# Write a status message to the console.
Write-Host "Changing directory to project root: $projectPath" -ForegroundColor Yellow

# Change the current directory to the project root. Includes error handling.
try {
    Set-Location -Path $projectPath -ErrorAction Stop
}
catch {
    Write-Host "FATAL ERROR: Could not find the project path '$projectPath'." -ForegroundColor Red
    Write-Host "Please edit this script and correct the path in the '$projectPath' variable." -ForegroundColor Red
    Read-Host -Prompt "Press Enter to exit"
    exit
}

# Write a message indicating the next step.
Write-Host "Launching the Face Recognition application..." -ForegroundColor Green

# --- Conda Environment Execution ---
$condaEnvName = "cv_env"

# Check if Conda is installed and available in the PATH.
if (-not (Get-Command conda -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Conda is not found. Please ensure Conda is installed and its 'condabin' directory is in your system's PATH." -ForegroundColor Red
    Write-Host "You may need to run 'conda init powershell' in a terminal and restart it." -ForegroundColor Red
    Read-Host -Prompt "Press Enter to exit"
    exit
}

# --- Find Conda Environment's Python Executable ---
# This method is more reliable for scripts than using 'conda run' or hooks.
$pythonExecutable = $null
try {
    # Get conda environment info as JSON and find the path for our target environment.
    $condaInfoJson = conda env list --json | ConvertFrom-Json
    $envPath = $condaInfoJson.envs | Where-Object { ($_ -split '[\/|\\]')[-1] -eq $condaEnvName } | Select-Object -First 1

    if ($envPath) {
        $pythonExecutable = Join-Path -Path $envPath -ChildPath "python.exe"
    }
} catch {
    # This catch block will trigger if 'conda' command fails or JSON conversion fails.
    Write-Host "ERROR: Failed to process Conda environment list. Is Conda installed and working correctly?" -ForegroundColor Red
    Read-Host -Prompt "Press Enter to exit"
    exit
}

# Check if the Python executable was found in the target environment.
if (-not ($pythonExecutable) -or -not (Test-Path $pythonExecutable)) {
    Write-Host "ERROR: Could not find 'python.exe' in Conda environment '$condaEnvName'." -ForegroundColor Red
    Write-Host "Please ensure the environment exists and contains a Python installation." -ForegroundColor Red
    Read-Host -Prompt "Press Enter to exit"
    exit
}

# Run the Python GUI application using the specified Conda environment.
Write-Host "Using Python from Conda environment: '$condaEnvName'" -ForegroundColor Cyan
& $pythonExecutable src/app_gui.py

Write-Host "Application has been closed." -ForegroundColor Yellow