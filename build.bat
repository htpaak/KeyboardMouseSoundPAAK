@echo off
REM 현재 배치 파일의 디렉토리로 이동
cd /d "%~dp0"

REM 기존 빌드 아티팩트 제거 (spec 파일은 유지)
echo Cleaning up previous build artifacts...
if exist "__pycache__" (
    echo Removing __pycache__ directory...
    rd /s /q "__pycache__"
)
if exist "build" (
    echo Removing build directory...
    rd /s /q "build"
)
if exist "dist" (
    echo Removing dist directory...
    rd /s /q "dist"
)
echo.

echo Checking and installing PyInstaller if necessary...
REM PyInstaller 설치 확인 및 자동 설치
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo PyInstaller is not installed. Installing it now...
    pip install pyinstaller
    if %errorlevel% neq 0 (
        echo Failed to install PyInstaller. Exiting.
        pause
        exit /b %errorlevel%
    )
)

echo Building the application...

REM KeyboardMouseSoundPAAK.spec 파일이 존재하는지 확인
if exist "KeyboardMouseSoundPAAK.spec" (
    echo Using existing spec file KeyboardMouseSoundPAAK.spec
) else (
    REM spec 파일이 없으면 새로 생성하고 관리자 권한 추가
    echo Creating new spec file...
    pyi-makespec --noconsole ^
      --onefile ^
      --icon="assets/icon.ico" ^
      --add-data "assets;assets" ^
      --add-data "src;src" ^
      --name="KeyboardMouseSoundPAAK" ^
      main.py

    REM 생성된 spec 파일 수정해 관리자 권한 요청 추가
    echo Adding admin privileges to spec file...
    powershell -Command "(Get-Content KeyboardMouseSoundPAAK.spec) -replace 'icon=\[''assets\\\\icon.ico''\],', 'icon=[''assets\\\\icon.ico''], uac_admin=True,' | Set-Content KeyboardMouseSoundPAAK.spec"
)

REM spec 파일로 빌드
echo Building from spec file...
pyinstaller --clean KeyboardMouseSoundPAAK.spec

echo.
REM 빌드 성공/실패 확인
if %errorlevel% equ 0 (
    echo Build completed successfully!
    echo Executable can be found in the 'dist' folder.
) else (
    echo Build failed with error code %errorlevel%.
)

pause 