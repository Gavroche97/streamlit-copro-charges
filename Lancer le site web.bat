@echo off
setlocal
cd /d "%~dp0"
echo Lancement de l'application Streamlit dans une nouvelle fenetre...
set "URL=http://localhost:8501"

where py >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "STREAMLIT_CMD=py -3 -m streamlit run ""app.py"" --server.port 8501"
) else (
    set "STREAMLIT_CMD=python -m streamlit run ""app.py"" --server.port 8501"
)
start "Streamlit" cmd /k %STREAMLIT_CMD%
echo.
echo Attente du demarrage du serveur Streamlit...
set /a TIMEOUT=60
set /a INTERVAL=5
set /a ELAPSED=0
:WAIT_LOOP
powershell -Command "try { Invoke-WebRequest -Uri '%URL%' -UseBasicParsing -TimeoutSec 5 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if %ERRORLEVEL% equ 0 goto OPEN_BROWSER
if %ELAPSED% geq %TIMEOUT% goto TIMEOUT_ERROR
timeout /t %INTERVAL% /nobreak >nul
set /a ELAPSED+=INTERVAL
goto WAIT_LOOP

:OPEN_BROWSER
echo Serveur demarre. Ouverture du navigateur par defaut...
start "" "%URL%"
goto END

:TIMEOUT_ERROR
echo Le serveur Streamlit n'a pas repondu apres %TIMEOUT% secondes.
echo Verifiez la fenetre Streamlit pour les messages d'erreur.
pause

:END
