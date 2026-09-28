# Checkerz Run Club Event Management

Checkerz Run Club (CRC) needs a simple way to organize running events, register members, collect fees, and check attendees in. This Django application supports that flow for the club in Hubli/Dharwad.

## Features

- Member signup and login, with duplicate-email and phone-number validation.
- Upcoming event list with available spots and event fees.
- Member registrations, QR codes, and a personal registration list.
- Razorpay checkout for paid events; free events do not require checkout.
- Signature-verified payment confirmation.
- Staff-only QR check-in and event organizer roster with payment and attendance counts.
- Django admin for managing members, events, registrations, payments, and attendance.
    

## Technology

- Python 3.13 and Django 6.1
- Bootstrap 5 via CDN
- SQLite for local development; PostgreSQL in the hosted deployment
- Razorpay for event payments
- `qrcode` for registration QR codes
- Whitenoise for static files and Gunicorn for the web process
- Render deployment: [crc-project.onrender.com](https://crc-project.onrender.com)

## Local setup

Prerequisites: Python 3.13 and Git. From the project directory in PowerShell:

```powershell
py -3.13 -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
venv\Scripts\python.exe manage.py migrate
venv\Scripts\python.exe manage.py createsuperuser
venv\Scripts\python.exe manage.py runserver
```

Open `http://127.0.0.1:8000/`. Local development uses SQLite by default. To run checks and tests:

```powershell
venv\Scripts\python.exe manage.py check
venv\Scripts\python.exe manage.py test
```

Paid checkout needs Razorpay test credentials configured in the local environment. Never put credential values in source control.

## Environment variable names

Configure values in the environment that runs Django. This project uses these names:

- `DATABASE_URL`
- `SECRET_KEY`
- `DEBUG`
- `RAZORPAY_KEY_ID`
- `RAZORPAY_KEY_SECRET`

Do not commit environment variable values. Local SQLite is used when `DATABASE_URL` is not configured.

## Deployment

The hosted application is at [https://crc-project.onrender.com](https://crc-project.onrender.com). The Render deployment uses PostgreSQL and collects static files before serving the application. Changes to the production branch may trigger deployment, so verify changes locally first.