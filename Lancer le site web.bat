@echo off
setlocal
cd /d "%~dp0"
echo Lancement de l'application Streamlit dans une nouvelle fenetre...
set "STREAMLIT_CMD=py -3 -m streamlit run ""app.py"" --server.port 8501"
start "Streamlit" cmd /c %STREAMLIT_CMD%
if %ERRORLEVEL% neq 0 (
    echo.
    echo "py -3" a echoue, tentative avec python...
    set "STREAMLIT_CMD=python -m streamlit run ""app.py"" --server.port 8501"
    start "Streamlit" cmd /c %STREAMLIT_CMD%
    if %ERRORLEVEL% neq 0 (
        echo.
        echo Impossible de lancer Streamlit. Verifiez que Python est installe et que les dependances sont disponibles.
        pause
        exit /b 1
    )
)
echo Attente du demarrage du serveur...
timeout /t 5 /nobreak >nul
echo Ouverture du site dans le navigateur par defaut...
start "" "http://localhost:8501"
