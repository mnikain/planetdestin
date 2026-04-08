## Beachfront Vacation Rental Website

This is a small Django-powered website for a beachfront vacation rental company.
It includes:

- A modern, mobile-friendly marketing site highlighting the views and amenities.
- A secure renter portal where guests can register, log in, and view:
  - Door entry code
  - Pool access code
  - Wi-Fi details
  - House manual / check-in instructions

### 1. Prerequisites

- Python 3.10+ installed
- `pip` available on your system

### 2. Setup

```bash
cd "path/to/Dev/planetdestin1"

# (Optional but recommended) create a virtualenv
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Create the database and superuser

```bash
cd beach_rental_site
python manage.py migrate
python manage.py createsuperuser
```

The superuser lets you log into the Django admin at `/admin/` and is also useful
for managing users and content.

### 4. Configure renter-only info (codes, Wi‑Fi, instructions)

The renter dashboard pulls sensitive info from environment variables so you
don’t have to hard-code them:

- `RENTER_ENTRY_CODE`
- `POOL_ACCESS_CODE`
- `WIFI_NETWORK_NAME`
- `WIFI_PASSWORD`
- `HOUSE_MANUAL_TEXT`

You can set them in your shell before running the server, for example:

```bash
export RENTER_ENTRY_CODE="1234#"
export POOL_ACCESS_CODE="POOL-5678"
export WIFI_NETWORK_NAME="BeachHouseWifi"
export WIFI_PASSWORD="SuperSecretPassword"
export HOUSE_MANUAL_TEXT="Welcome to our beach home! Check-in is after 3pm..."
```

On Windows (PowerShell), use:

```powershell
$env:RENTER_ENTRY_CODE = "1234#"
```

### 5. Run the development server

From the `beach_rental_site` directory:

```bash
python manage.py runserver
```

Then open `http://127.0.0.1:8000/` in your browser.

- Public marketing homepage: `/`
- Renter registration: `/register/`
- Renter login: `/login/`
- Renter dashboard (requires login): `/dashboard/`
- Django admin: `/admin/`

### 6. Workflow for renters

1. Guest visits the site and can browse photos, amenities, and details.
2. You (or they) create an account via **Register**.
3. Guest logs in and is redirected to the **Renter Dashboard**.
4. The dashboard shows the current codes, Wi‑Fi info, and house manual text.

You can change the sensitive values at any time by updating the environment
variables and restarting the server.

########## additional mo notes
to get around the arm64 issues, installed mysqlconnector python version:

  pip install mysql-connector-python  
  
then in settings.py, change the engine to:         "ENGINE": "mysql.connector.django",

