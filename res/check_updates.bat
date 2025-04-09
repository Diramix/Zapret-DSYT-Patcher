@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] This script is not running as Administrator. Restarting with elevated privileges...
    powershell -Command "Start-Process '%~dpnx0' -Verb runAs"
    exit /b
)

set "MERGE_FILES=list-general.txt ipset-cloudflare.txt ipset-discord.txt list-discord.txt"
set "GITHUB_REPO=https://github.com/Flowseal/zapret-discord-youtube/releases/download"
set "GITHUB_API_URL=https://api.github.com/repos/Flowseal/zapret-discord-youtube/releases/latest"
set "LOCAL_DIR=%~dp0"
set "LOCAL_DIR=%LOCAL_DIR:~0,-1%"
set "TEMP_DIR=%TEMP%\zapret_update_%random%"
set "SCRIPT_NAME=%~nx0"
set "SOFT_MODE=0"
if "%~1"=="soft" set "SOFT_MODE=1"

title Zapret

:: Проверяем наличие curl
where curl >nul 2>&1 || (
    echo [ERROR] curl not found. Install from: https://curl.se/
    exit /b 1
)

:: Получаем локальную версию из файла version.txt
set "LOCAL_VERSION="
for /f "delims=" %%A in (%LOCAL_DIR%\res\version.txt) do (
    set "LOCAL_VERSION=%%A"
)
set "LOCAL_VERSION=%LOCAL_VERSION: =%"

:: Проверяем версию на GitHub
echo [INFO] Checking latest version from GitHub...
for /f "tokens=2 delims=:," %%A in ('curl -s "%GITHUB_API_URL%" ^| findstr /i "\"tag_name\""') do (
    set "GITHUB_VERSION=%%A"
)
set GITHUB_VERSION=%GITHUB_VERSION:"=%
set GITHUB_VERSION=%GITHUB_VERSION: =%

echo [INFO] Local version: %LOCAL_VERSION%
echo [INFO] Latest GitHub version: %GITHUB_VERSION%

if "%LOCAL_VERSION%"=="%GITHUB_VERSION%" (
    echo [INFO] You are already using the latest version: %LOCAL_VERSION%
    exit /b 0
)

:: Запрашиваем у пользователя обновление
set /p user_input=New version found. Do you want to update? (Y/n): 
if /i "!user_input!"=="n" (
    echo Update canceled.
    exit /b 0
)
if /i not "!user_input!"=="y" (
    echo Invalid input. Exiting.
    exit /b 1
)

title Zapret %GITHUB_VERSION%

set "NEED_RESTART_SERVICE=0"
setlocal enabledelayedexpansion
set "ServiceState="

for %%S in (zapret WinDivert) do (
    for /f "tokens=3 delims=: " %%A in ('sc query "%%S" ^| findstr /i "STATE"') do (
        set "ServiceState=%%A"
    )
    set "ServiceState=!ServiceState: =!"
    if /i "!ServiceState!"=="RUNNING" (
        echo [INFO] Service %%S is currently RUNNING, stopping temporarily...
        net stop "%%S" >nul 2>&1 || echo [ERROR] Failed to stop service %%S.
        endlocal & set "NEED_RESTART_SERVICE=1" & setlocal enabledelayedexpansion
    ) else (
        echo [INFO] Service %%S is NOT running.
    )
)
endlocal

set "DOWNLOAD_URL=%GITHUB_REPO%/%GITHUB_VERSION%/zapret-discord-youtube-%GITHUB_VERSION%.zip"

echo [1/4] Creating temp directory...
mkdir "%TEMP_DIR%" 2>nul || (
    echo [ERROR] Failed to create temp directory.
    exit /b 1
)

echo [INFO] Archiving current files...
powershell -Command "Compress-Archive -Path '%LOCAL_DIR%\*' -DestinationPath '%LOCAL_DIR%\zapret-old.zip' -Force"

echo [INFO] Downloading: %DOWNLOAD_URL%...
curl -s -L -o "%TEMP_DIR%\zapret-discord-youtube-%GITHUB_VERSION%.zip" "%DOWNLOAD_URL%" || (
    echo [ERROR] Download failed.
    rmdir /s /q "%TEMP_DIR%" 2>nul
    exit /b 1
)

echo [INFO] Extracting ZIP file...
powershell -Command "$zipPath = '%TEMP_DIR%\zapret-discord-youtube-%GITHUB_VERSION%.zip'; $destPath = '%TEMP_DIR%'; Add-Type -AssemblyName System.IO.Compression.FileSystem; $encoding = [System.Text.Encoding]::GetEncoding('cp866'); [System.IO.Compression.ZipFile]::ExtractToDirectory($zipPath, $destPath, $encoding)"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to extract ZIP file.
    rmdir /s /q "%TEMP_DIR%" 2>nul
    exit /b 1
)

echo [3/4] Copying files...
robocopy "%TEMP_DIR%" "%LOCAL_DIR%" /E /NDL /NFL /NJH /NJS /NP ^
    /XD ".git" ".service" ^
    /XF "zapret-discord-youtube-%GITHUB_VERSION%.zip" ".gitignore" "LICENSE.txt" "README.md" "%SCRIPT_NAME%" "check_updates.bat" "check_updates.old" >nul

echo [4/4] Merging special files...
for %%f in (%MERGE_FILES%) do (
    if exist "%TEMP_DIR%\%%f" (
        if exist "%LOCAL_DIR%\%%f" (
            echo [Merging] %%f
            call :MergeFiles "%LOCAL_DIR%\%%f" "%TEMP_DIR%\%%f" "%LOCAL_DIR%\%%f"
        ) else (
            echo [Copying] %%f
            copy "%TEMP_DIR%\%%f" "%LOCAL_DIR%\%%f"
        )
    )
)

echo [INFO] Deleting temporary files...
del /f /q "%TEMP_DIR%\zapret-discord-youtube-%GITHUB_VERSION%.zip"
rmdir /s /q "%TEMP_DIR%" 2>nul

:: Обновляем версию в файле version.txt
echo [INFO] Updating version in version.txt...
echo %GITHUB_VERSION% > "%LOCAL_DIR%\res\version.txt"

if "%NEED_RESTART_SERVICE%"=="1" (
    echo [INFO] Restarting services...
    net start "zapret" >nul 2>&1 || echo [ERROR] Failed to start service zapret.
)

if "%SOFT_MODE%"=="0" (
    echo [SUCCESS] Update completed!
    start "" "%LOCAL_DIR%\res\web\index.html"
)

exit /b 0

:MergeFiles
setlocal disabledelayedexpansion
set "user_file=%~1"
set "new_file=%~2"
set "output_file=%~3"
set "temp_file=%TEMP%\%random%.tmp"

if exist "%new_file%" (
    copy /y "%new_file%" "%temp_file%" >nul
    for /f "delims=" %%l in ('type "%temp_file%"') do set "last_line=%%l"
    >>"%temp_file%" echo(
) else (
    echo [ERROR] Source file not found: %new_file%
    endlocal
    goto :eof
)

if exist "%user_file%" (
    setlocal enabledelayedexpansion
    for /f "tokens=* delims=" %%a in ('type "%user_file%"') do (
        set "line=%%a"
        if defined line (
            findstr /x /c:"!line!" "%temp_file%" >nul || >>"%temp_file%" echo(!line!
        )
    )
    endlocal
)

move /y "%temp_file%" "%output_file%" >nul
endlocal
goto :eof
