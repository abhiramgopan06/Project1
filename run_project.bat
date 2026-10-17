@echo off
cd /d "%~dp0"
echo Checking and repairing database fields...
python repair_database.py
if errorlevel 1 (
  echo Database repair failed. Check the error above.
  pause
  exit /b 1
)
echo Starting Django development server...
python manage.py runserver
pause
