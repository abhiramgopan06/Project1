# ShopEasy - Local Setup and Migration Fix

## 1. Open the project
Open PowerShell in the folder containing `manage.py`.

## 2. Activate your existing virtual environment
If the environment folder is named `env`:
```powershell
.\env\Scripts\Activate.ps1
```
If PowerShell blocks activation for this session:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\env\Scripts\Activate.ps1
```

## 3. Install dependencies
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Copy `.env.example` to `.env` if you need local environment settings, then fill in your own values. Do not share `.env` or API keys.

## 4. Back up the database before migration
If the project uses `db.sqlite3`, close the server and make a copy:
```powershell
Copy-Item .\db.sqlite3 .\db.sqlite3.backup
```
If the database file has a different name, back up that file instead.

## 5. Apply migrations
This archive fixes a duplicate cart migration branch that attempted to remove `unique_product_per_cart` twice.
```powershell
python manage.py showmigrations cart
python manage.py migrate
python manage.py check
python manage.py runserver
```

If `migrate` still fails, do not delete the database or migration files. Copy the complete new traceback and the output of `python manage.py showmigrations cart`. A database may contain real customer/order data.

## Notes
- `.git`, local virtual environments, cached bytecode, and collected `staticfiles` are intentionally not included in this ZIP.
- Test payment credentials and email credentials must be configured separately; real payment/email delivery cannot be confirmed without those credentials.
