Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ScriptDir = $PSScriptRoot
if (-not $ScriptDir) {
    $ScriptDir = Split-Path -Path $MyInvocation.MyCommand.Path -Parent
}
Write-Host "Script directory: $ScriptDir" -ForegroundColor Cyan

$RequiredPythonVersion = '3.9.11'

$VenvDirName = ".venv"
$RequirementsFileName = "Windows_requirements.txt"
$MainScriptName = "Windows_main.py"
$BuildName = "ColonyDynamicsSimulator"
$IconWinRelPath = "img\icon.ico"
$ItemsToCopyRel = @(".env", "img", "Template")
$DistDirName = "Windows_dist"
$BuildDirName = "build"

$VenvDir = Join-Path $ScriptDir $VenvDirName
$RequirementsFile = Join-Path $ScriptDir $RequirementsFileName
$MainScript = Join-Path $ScriptDir $MainScriptName
$IconWin = Join-Path $ScriptDir $IconWinRelPath
$ItemsToCopy = $ItemsToCopyRel | ForEach-Object { Join-Path $ScriptDir $_ }
$BuildDistDir = Join-Path $ScriptDir $DistDirName
$BuildDir = Join-Path $ScriptDir $BuildDirName
$SpecFile = Join-Path $ScriptDir "$($BuildName).spec"

$ParentDir = Split-Path -Path $ScriptDir -Parent
if (-not $ParentDir) {
    Write-Error "*** ERROR: Could not determine parent directory of '$ScriptDir'. Cannot proceed. ***"
    exit 1
}
$FinalDistPath = Join-Path $ParentDir $DistDirName 
$PythonExe = $null
$PipExe = $null
$PyInstallerExe = $null

function Invoke-CommandAndCheck {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Command,
        [Parameter(Mandatory=$false)]
        [string[]]$Arguments,
        [Parameter(Mandatory=$true)]
        [string]$ErrorMessage
    )
    Write-Host "Executing: $Command $($Arguments -join ' ')" -ForegroundColor Gray
    try {
        & $Command $Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "$ErrorMessage (Exit Code: $LASTEXITCODE)"
        }
        Write-Host "`t -> Success." -ForegroundColor Green
    } catch {
        Write-Error "`n*** ERROR: $($_.Exception.Message) ***`n"
        exit 1
    }
}

Write-Host "`n=== Windows Setup Script (PowerShell Automatic) ===" -ForegroundColor Yellow

#region 0.5. Clean Previous Build Output (in parent directory)
Write-Host "`n--- 0.5. Cleaning up previous build output ('$DistDirName' in parent dir) ---" -ForegroundColor Magenta
Write-Host "Checking for existing build output at: $FinalDistPath"
if (Test-Path $FinalDistPath) {
    Write-Warning "WARNING: Found previous build output at '$FinalDistPath'. Attempting to remove it."
    try {
        Remove-Item -Path $FinalDistPath -Recurse -Force -ErrorAction Stop
        Write-Host "`t -> Previous build output removed successfully." -ForegroundColor Green
    } catch {
        Write-Error "*** ERROR: Failed to remove previous build output at '$FinalDistPath'. Check permissions or if files are in use. Error: $($_.Exception.Message) ***"
        exit 1 # Explicit exit just in case
    }
} else {
    Write-Host "No previous build output found at '$FinalDistPath'."
}
#endregion

#region 1. Clean existing virtual environment (in app directory)
Write-Host "`n--- 1. Cleaning up existing environment (in '$ScriptDir') ---" -ForegroundColor Magenta
if (Test-Path $VenvDir -PathType Container) {
    Write-Host "Removing existing virtual environment: $VenvDir"
    try {
        Remove-Item -Path $VenvDir -Recurse -Force -ErrorAction Stop
        Write-Host "`t -> Virtual environment removed." -ForegroundColor Green
    } catch {
        Write-Error "*** ERROR: Failed to remove existing virtual environment '$VenvDir'. Check permissions or if files are in use. Error: $($_.Exception.Message) ***"
        exit 1
    }
} else {
    Write-Host "No existing virtual environment found at '$VenvDir'."
}
#endregion

#region 2. Verify Python Installation and Version
Write-Host "`n--- 2. Verifying Python installation and version ---" -ForegroundColor Magenta
$PythonCommand = Get-Command python -ErrorAction SilentlyContinue
if ($null -eq $PythonCommand) {
    Write-Error "*** ERROR: Python not found in system PATH. Please install Python $RequiredPythonVersion and ensure it's added to PATH. ***"
    exit 1
}
$PythonPath = $PythonCommand.Source
Write-Host "Python executable found: $PythonPath"
try {
    Write-Host "Checking Python version..."
    $PythonVersionOutput = & $PythonPath --version 2>&1
    Write-Host "Output from '$PythonPath --version': $PythonVersionOutput"
    if ($PythonVersionOutput -match '(\d+\.\d+\.\d+)') {
        $DetectedPythonVersion = $matches[1]
        Write-Host "Detected Python version: $DetectedPythonVersion"
        if ($DetectedPythonVersion -eq $RequiredPythonVersion) {
            Write-Host "Python version $DetectedPythonVersion matches required version $RequiredPythonVersion." -ForegroundColor Green
        } else {
            Write-Error "*** ERROR: Incorrect Python version detected. Found '$DetectedPythonVersion', but require '$RequiredPythonVersion'. Please install or configure PATH to use the correct version. ***"
            exit 1
        }
    } else {
        Write-Error "*** ERROR: Could not parse Python version number from output: '$PythonVersionOutput'. Ensure '$PythonPath --version' works correctly. ***"
        exit 1
    }
} catch {
    Write-Error "*** ERROR: Failed to execute or parse '$PythonPath --version'. Error: $($_.Exception.Message) ***"
    exit 1
}
#endregion

#region 3. Create new virtual environment
Write-Host "`n--- 3. Creating new virtual environment ---" -ForegroundColor Magenta
Invoke-CommandAndCheck -Command $PythonPath -Arguments '-m', 'venv', """$VenvDir""" -ErrorMessage "Virtual environment creation in '$VenvDir' failed"
$PythonExe = Join-Path $VenvDir "Scripts\python.exe"
$PipExe = Join-Path $VenvDir "Scripts\pip.exe"
$PyInstallerExe = Join-Path $VenvDir "Scripts\pyinstaller.exe"
if (-not (Test-Path $PythonExe -PathType Leaf)) {
     Write-Error "*** ERROR: python.exe not found in the created virtual environment: '$PythonExe' ***"
     exit 1
}
Write-Host "Venv Python path: $PythonExe"
#endregion

#region 4. Install/Upgrade Base Packages
Write-Host "`n--- 4. Upgrading pip, setuptools, wheel ---" -ForegroundColor Magenta
Invoke-CommandAndCheck -Command $PythonExe -Arguments '-m', 'pip', 'install', '--upgrade', 'pip', 'setuptools', 'wheel' -ErrorMessage "Upgrade of base packages (pip, setuptools, wheel) failed"
#endregion

#region 5. Install PyInstaller
Write-Host "`n--- 5. Installing PyInstaller ---" -ForegroundColor Magenta
Invoke-CommandAndCheck -Command $PipExe -Arguments 'install', 'pyinstaller' -ErrorMessage "PyInstaller installation failed"
if (-not (Test-Path $PyInstallerExe -PathType Leaf)) {
     Write-Warning "WARNING: pyinstaller.exe not found after installation at: '$PyInstallerExe'. The build might fail."
}
#endregion

#region 6. Install Dependencies from windows_requirements.txt
Write-Host "`n--- 6. Installing dependencies from '$($RequirementsFileName)' ---" -ForegroundColor Magenta
if (Test-Path $RequirementsFile -PathType Leaf) {
    Invoke-CommandAndCheck -Command $PipExe -Arguments 'install', '--no-cache-dir', '-r', $RequirementsFile -ErrorMessage "Installation of dependencies from '$RequirementsFileName' failed"
} else {
    Write-Warning "WARNING: File '$RequirementsFileName' not found. Skipping dependency installation."
}
#endregion

#region 7. Verify Main Script for Build
Write-Host "`n--- 7. Verifying main script for build ---" -ForegroundColor Magenta
if (-not (Test-Path $MainScript -PathType Leaf)) {
    Write-Error "*** ERROR: Main script '$MainScriptName' not found in '$ScriptDir'. Cannot proceed with build. ***"
    exit 1
}
 Write-Host "Main script found: $MainScript"
#endregion

#region 8. Build with PyInstaller
Write-Host "`n--- 8. Building executable with PyInstaller ---" -ForegroundColor Magenta
$PyInstallerArgs = @(
    '--onefile',
    '--windowed',
    "--name=$BuildName",
    '--noconfirm',
    "--distpath=$BuildDistDir"
)
if (Test-Path $IconWin -PathType Leaf) {
    Write-Host "Adding icon: $IconWin"
    $PyInstallerArgs += "--icon=""$IconWin"""
} else {
    Write-Warning "WARNING: Icon file '$IconWin' not found. Building without icon."
}
$PyInstallerArgs += """$MainScript"""
Invoke-CommandAndCheck -Command $PyInstallerExe -Arguments $PyInstallerArgs -ErrorMessage "PyInstaller build failed"
#endregion

#region 9. Copy Additional Items to Windows_dist Folder (Temporary in 'app')
Write-Host "`n--- 9. Copying additional items to '$DistDirName' folder (temporary in 'app') ---" -ForegroundColor Magenta
if (-not (Test-Path $BuildDistDir -PathType Container)) {
     Write-Error "*** ERROR: PyInstaller output directory '$BuildDistDir' not found after build. ***"
     exit 1
}
 Write-Host "Temporary output directory found: $BuildDistDir"
foreach ($itemSourcePath in $ItemsToCopy) {
    $itemName = Split-Path $itemSourcePath -Leaf
    if (Test-Path $itemSourcePath) {
        $destinationDir = $BuildDistDir
        Write-Host "Copying '$itemName' to '$destinationDir'..."
        try {
            Copy-Item -Path $itemSourcePath -Destination $destinationDir -Recurse -Force -ErrorAction Stop
            Write-Host "`t -> Successfully copied '$itemName'." -ForegroundColor Green
        } catch {
             Write-Warning "WARNING: Failed to copy '$itemName'. Error: $($_.Exception.Message)"
        }
    } else {
        Write-Warning "WARNING: Source item '$itemSourcePath' not found. Skipping copy."
    }
}
#endregion

#region 10. Cleanup Intermediate Files (in 'app')
Write-Host "`n--- 10. Cleaning up intermediate files (in 'app') ---" -ForegroundColor Magenta
if (Test-Path $BuildDir -PathType Container) {
    Write-Host "Removing build directory: $BuildDir"
    Remove-Item -Path $BuildDir -Recurse -Force -ErrorAction SilentlyContinue
    if ($?) { Write-Host "`t -> Build directory removed." -ForegroundColor Green } else { Write-Warning "Could not remove build directory $BuildDir."}
} else {
     Write-Host "Build directory '$BuildDir' not found, skipping cleanup."
}
if (Test-Path $SpecFile -PathType Leaf) {
     Write-Host "Removing spec file: $SpecFile"
     Remove-Item -Path $SpecFile -Force -ErrorAction SilentlyContinue
     if ($?) { Write-Host "`t -> Spec file removed." -ForegroundColor Green } else { Write-Warning "Could not remove spec file $SpecFile."}
} else {
     Write-Host "Spec file '$SpecFile' not found, skipping cleanup."
}
#endregion

#region 11. Move Windows_dist Folder to Parent Level
Write-Host "`n--- 11. Moving '$DistDirName' folder to parent level ---" -ForegroundColor Magenta
Write-Host "Final destination directory: $FinalDistPath"

if (-not (Test-Path $BuildDistDir -PathType Container)) {
    Write-Error "*** ERROR: Source folder '$BuildDistDir' created by PyInstaller not found for moving. ***"
}

Write-Host "Moving '$BuildDistDir' to '$ParentDir'..."
try {
    Move-Item -Path $BuildDistDir -Destination $ParentDir -ErrorAction Stop
    Write-Host "`t -> '$DistDirName' folder moved successfully to '$ParentDir'." -ForegroundColor Green
} catch {
     Write-Error "*** ERROR: Failed to move '$BuildDistDir' folder to '$ParentDir'. Error: $($_.Exception.Message) ***"
}
#endregion

#region 12. Final Cleanup (.venv in 'app')
Write-Host "`n--- 12. Final Virtual Environment Cleanup ---" -ForegroundColor Magenta
if (Test-Path $VenvDir -PathType Container) {
    Write-Host "Removing virtual environment: $VenvDir"
    Remove-Item -Path $VenvDir -Recurse -Force -ErrorAction SilentlyContinue
    if ($?) {
        Write-Host "`t -> Virtual environment removed." -ForegroundColor Green
    } else {
        Write-Warning "Could not completely remove virtual environment '$VenvDir'. You may need to remove it manually."
    }
} else {
    Write-Host "Virtual environment '$VenvDir' not found, skipping final cleanup."
}
#endregion

$FinalDistPathMsg = Join-Path $ParentDir $DistDirName

Write-Host "`n=== Script finished successfully! ===" -ForegroundColor Yellow
Write-Host "The final '$DistDirName' folder with the build is located at: $FinalDistPathMsg" -ForegroundColor Green
exit 0