@echo off
cd /d "%~dp0"
echo Applying database migrations...
python manage.py migrate
if errorlevel 1 (
  echo Migration failed. Check the error above.
  pause
  exit /b 1
)
echo Starting Django development server...
python manage.py runserver
pause
