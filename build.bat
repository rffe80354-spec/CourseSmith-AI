@echo off
REM ============================================
REM CourseSmith AI - Build Script for Windows
REM ============================================
REM This script builds both applications using PyInstaller.
REM
REM Prerequisites:
REM   - Python 3.x installed
REM   - pip install pyinstaller
REM   - All dependencies from requirements.txt installed
REM
REM Usage:
REM   build.bat           - Build both applications
REM   build.bat main      - Build only CourseSmith_v2
REM   build.bat keygen    - Build only KeyGen_Admin
REM   build.bat clean     - Clean build artifacts
REM ============================================

echo ============================================
echo CourseSmith AI Build Script
echo ============================================

REM Check if PyInstaller is installed
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo ERROR: PyInstaller is not installed.
    echo Please run: pip install pyinstaller
    exit /b 1
)

REM Handle command line arguments
if "%1"=="clean" goto :clean
if "%1"=="main" goto :build_main
if "%1"=="keygen" goto :build_keygen

REM Default: build both
goto :build_all

:clean
echo Cleaning build artifacts...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "*.spec" del /q "*.spec" 2>nul
echo Clean complete!
goto :end

:build_main
echo Building CourseSmith_v2...
pyinstaller --clean --noconfirm CourseSmith_v2.spec
if errorlevel 1 (
    echo ERROR: Build failed for CourseSmith_v2
    exit /b 1
)
echo CourseSmith_v2 build complete!
goto :end

:build_keygen
echo Building KeyGen_Admin...
pyinstaller --clean --noconfirm KeyGen_Admin.spec
if errorlevel 1 (
    echo ERROR: Build failed for KeyGen_Admin
    exit /b 1
)
echo KeyGen_Admin build complete!
goto :end

:build_all
echo Building CourseSmith_v2...
pyinstaller --clean --noconfirm CourseSmith_v2.spec
if errorlevel 1 (
    echo ERROR: Build failed for CourseSmith_v2
    exit /b 1
)
echo CourseSmith_v2 build complete!

echo.
echo Building KeyGen_Admin...
pyinstaller --clean --noconfirm KeyGen_Admin.spec
if errorlevel 1 (
    echo ERROR: Build failed for KeyGen_Admin
    exit /b 1
)
echo KeyGen_Admin build complete!

echo.
echo ============================================
echo All builds completed successfully!
echo Output files are in the 'dist' folder:
echo   - dist/CourseSmith_v2.exe
echo   - dist/KeyGen_Admin.exe
echo ============================================
goto :end

:end
