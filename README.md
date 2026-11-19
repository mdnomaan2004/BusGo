# BusGo — Full-stack Bus Ticket Booking Project

BusGo is a learning/demo full-stack application built with **HTML, CSS, JavaScript, Python Flask and SQLite**. It follows the dark navy and blue design direction from the earlier project reference.

## Features
- Search demo buses by origin, destination and travel date
- View route, operator, timings, fare and remaining seats
- Live seat availability for a selected travel date
- Select up to six seats
- Enter passenger details and confirm a demo booking
- Save bookings in SQLite so they remain after restarting the app
- Retrieve a booking using its reference number
- Health endpoint at `/health`
- Responsive layout for desktop and mobile
- Dockerfile and Docker Compose setup for cloud deployment practice

## Project structure

```text
BusGo_Cloud_Project/
├── app.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── README.md
├── .gitignore
├── templates/
│   └── index.html
└── static/
    ├── css/
    │   └── style.css
    └── js/
        └── script.js
```

## Run locally on Windows

1. Install Python 3.10+.
2. Open PowerShell in this project folder.
3. Create a virtual environment:

   ```powershell
   python -m venv venv
   ```

4. Activate it:

   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and activate again.

5. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

6. Start the application:

   ```powershell
   python app.py
   ```

7. Open **http://127.0.0.1:5000** in Chrome.

Keep the PowerShell window running while using the site. To stop the server, press `Ctrl + C`.

## Try the booking flow
1. Search Mumbai → Pune for today or a future date.
2. Select a bus and choose one or more available seats.
3. Enter passenger name, email and phone.
4. Confirm the demo booking.
5. Copy the `BG` booking reference from the confirmation.
6. Use **My Bookings** to look up that reference.

The bus catalogue and fares are sample data. The project does not connect to a real bus operator or collect payments.

## Run with Docker

Install Docker Desktop, open a terminal in this folder, then run:

```powershell
docker compose up --build
```

Open http://127.0.0.1:5000. Stop with `Ctrl + C`; remove the container with `docker compose down`. The named Docker volume keeps the SQLite database across container recreation.

## Cloud project architecture (learning deployment)

**Browser → Flask/Gunicorn application → SQLite database file**

For a cloud-hosted learning deployment:
1. Push this project to a GitHub repository.
2. Create an AWS EC2 Linux instance.
3. Install Docker on the instance and allow inbound HTTP (port 80) plus SSH (port 22 restricted to your IP).
4. Deploy the container and place a reverse proxy such as Nginx in front of Gunicorn for HTTPS.
5. For a multi-user production deployment, replace SQLite with managed MySQL (Amazon RDS), move secrets to a secure secret store, add backups, monitoring and proper authentication/authorization.

## Important project limitations
- This is a **working student demo**, not a real ticketing service.
- Bus inventory is sample data held in `app.py`; no live operator API is connected.
- Payment is simulated; no payment gateway is connected.
- SQLite is suitable for local learning/demo use. For concurrent cloud use, use managed MySQL and migrations.
- Add real authentication, email/SMS notifications, cancellation/refund rules, rate limiting, CSRF protection, HTTPS and operational monitoring before production use.
- Set a strong `SECRET_KEY` environment variable before deployment.
