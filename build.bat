@echo off
REM ============================================
REM CourseSmith AI - Build Script for Windows
REM ============================================
REM This script builds both applications using PyInstaller.
REM It automatically installs all required dependencies.
REM
REM Prerequisites:
REM   - Python 3.x installed and in PATH
REM   - pip (comes with Python)
REM
REM Usage:
REM   build.bat           - Install deps and build all applications
REM   build.bat deps      - Only install dependencies
REM   build.bat main      - Build only CourseSmith_v2
REM   build.bat keygen    - Build only KeyGen_Admin
REM   build.bat clean     - Clean build artifacts
REM ============================================

echo ============================================
echo CourseSmith AI Build Script
echo ============================================
echo.

REM Handle command line arguments
if "%1"=="clean" goto :clean
if "%1"=="deps" goto :install_deps
if "%1"=="main" goto :build_main
if "%1"=="keygen" goto :build_keygen

REM Default: install deps and build all
goto :full_build

:install_deps
echo Installing dependencies from requirements.txt...
echo.
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies.
    echo Please check your internet connection and try again.
    exit /b 1
)
echo.
echo Dependencies installed successfully!
goto :end

:clean
echo Cleaning build artifacts...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
REM Clean all __pycache__ directories recursively
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
echo Clean complete!
goto :end

:build_main
echo Checking PyInstaller...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)
echo.
echo Building CourseSmith_v2...
pyinstaller --clean --noconfirm CourseSmith_v2.spec
if errorlevel 1 (
    echo ERROR: Build failed for CourseSmith_v2
    exit /b 1
)
echo CourseSmith_v2 build complete!
goto :end

:build_keygen
echo Checking PyInstaller...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)
echo.
echo Building KeyGen_Admin...
pyinstaller --clean --noconfirm KeyGen_Admin.spec
if errorlevel 1 (
    echo ERROR: Build failed for KeyGen_Admin
    exit /b 1
)
echo KeyGen_Admin build complete!
goto :end

:full_build
echo ============================================
echo Step 1: Cleaning Build Artifacts
echo ============================================
echo.

REM Clean __pycache__ and old build folders before starting
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
echo Clean complete!

echo.
echo ============================================
echo Step 2: Installing Dependencies
echo ============================================
echo.

REM Install all dependencies from requirements.txt
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies.
    exit /b 1
)
echo Dependencies installed successfully!

echo.
echo ============================================
echo Step 3: Building CourseSmith_v2
echo ============================================
echo.
pyinstaller --clean --noconfirm CourseSmith_v2.spec
if errorlevel 1 (
    echo ERROR: Build failed for CourseSmith_v2
    exit /b 1
)
echo CourseSmith_v2 build complete!

echo.
echo ============================================
echo Step 4: Building KeyGen_Admin
echo ============================================
echo.
pyinstaller --clean --noconfirm KeyGen_Admin.spec
if errorlevel 1 (
    echo ERROR: Build failed for KeyGen_Admin
    exit /b 1
)
echo KeyGen_Admin build complete!

echo.
echo ============================================
echo All builds completed successfully!
echo ============================================
echo.
echo Output files are in the 'dist' folder:
echo   - dist/CourseSmith_v2.exe
echo   - dist/KeyGen_Admin.exe
echo.
echo Before running, ensure you have:
echo   1. Created a .env file with your Supabase credentials
echo   2. Set up the 'secrets' table in Supabase with OPENAI_API_KEY
echo.
echo See .env.example for configuration details.
echo ============================================
goto :end

:end
