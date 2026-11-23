@echo off
cd /d "%~dp0"
if not exist .venv (python -m venv .venv)
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt || (echo No se instalaron dependencias. Comprueba Internet. & pause & exit /b 1)
if not exist data\admin.json (
  python manage.py init || (pause & exit /b 1)
)
start "" http://127.0.0.1:8000
python -m flask --app flask_backend run --host 127.0.0.1 --port 8000
pause
