import os, sqlite3, secrets, string
from datetime import datetime, date
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key-before-deployment")
DATABASE = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "busgo.db"))

BUS_CATALOG = [
    {"id": 1, "operator": "BlueLine Travels", "type": "AC Sleeper", "from": "Mumbai", "to": "Pune", "departure": "07:00", "arrival": "10:30", "duration": "3h 30m", "price": 499, "rating": 4.6, "total_seats": 36},
    {"id": 2, "operator": "Royal Express", "type": "AC Seater", "from": "Mumbai", "to": "Pune", "departure": "09:15", "arrival": "13:00", "duration": "3h 45m", "price": 399, "rating": 4.4, "total_seats": 40},
    {"id": 3, "operator": "Coastal Roadways", "type": "Volvo Multi-Axle", "from": "Mumbai", "to": "Goa", "departure": "20:00", "arrival": "08:00", "duration": "12h", "price": 1099, "rating": 4.8, "total_seats": 36},
    {"id": 4, "operator": "Deccan Connect", "type": "AC Sleeper", "from": "Pune", "to": "Mumbai", "departure": "08:30", "arrival": "12:00", "duration": "3h 30m", "price": 459, "rating": 4.5, "total_seats": 36},
    {"id": 5, "operator": "Nashik Travels", "type": "Non-AC Seater", "from": "Mumbai", "to": "Nashik", "departure": "06:45", "arrival": "10:45", "duration": "4h", "price": 299, "rating": 4.2, "total_seats": 40},
    {"id": 6, "operator": "Sunrise Bus Lines", "type": "AC Sleeper", "from": "Pune", "to": "Goa", "departure": "19:30", "arrival": "07:30", "duration": "12h", "price": 899, "rating": 4.7, "total_seats": 36},
    {"id": 7, "operator": "Western Star", "type": "AC Seater", "from": "Surat", "to": "Mumbai", "departure": "11:00", "arrival": "16:30", "duration": "5h 30m", "price": 549, "rating": 4.3, "total_seats": 40},
    {"id": 8, "operator": "CityLink", "type": "AC Sleeper", "from": "Mumbai", "to": "Surat", "departure": "22:00", "arrival": "04:30", "duration": "6h 30m", "price": 649, "rating": 4.5, "total_seats": 36},
]

def db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_ref TEXT UNIQUE NOT NULL,
            bus_id INTEGER NOT NULL,
            origin TEXT NOT NULL,
            destination TEXT NOT NULL,
            journey_date TEXT NOT NULL,
            operator TEXT NOT NULL,
            bus_type TEXT NOT NULL,
            departure TEXT NOT NULL,
            arrival TEXT NOT NULL,
            passenger_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            seats TEXT NOT NULL,
            total INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'CONFIRMED',
            created_at TEXT NOT NULL
        )""")

def get_bus(bus_id):
    return next((b for b in BUS_CATALOG if b["id"] == bus_id), None)

def booked_seats(bus_id, journey_date):
    with db() as conn:
        rows = conn.execute("SELECT seats FROM bookings WHERE bus_id=? AND journey_date=? AND status='CONFIRMED'", (bus_id, journey_date)).fetchall()
    result = set()
    for row in rows:
        result.update(row["seats"].split(","))
    return result

@app.context_processor
def inject_globals():
    return {"current_year": datetime.now().year}

@app.get("/")
def index():
    today = date.today().isoformat()
    return render_template("index.html", today=today)

@app.get("/api/buses")
def search_buses():
    origin = request.args.get("from", "").strip()
    destination = request.args.get("to", "").strip()
    journey_date = request.args.get("date", "").strip()
    if not origin or not destination or not journey_date:
        return jsonify({"error": "Please select origin, destination and journey date."}), 400
    if origin == destination:
        return jsonify({"error": "Origin and destination must be different."}), 400
    if journey_date < date.today().isoformat():
        return jsonify({"error": "Please select today or a future date."}), 400
    results = []
    for bus in BUS_CATALOG:
        if bus["from"] == origin and bus["to"] == destination:
            occupied = booked_seats(bus["id"], journey_date)
            item = dict(bus)
            item["available_seats"] = bus["total_seats"] - len(occupied)
            results.append(item)
    return jsonify({"buses": results, "from": origin, "to": destination, "date": journey_date})

@app.get("/api/buses/<int:bus_id>/seats")
def seats(bus_id):
    bus = get_bus(bus_id)
    journey_date = request.args.get("date", "")
    if not bus or not journey_date:
        return jsonify({"error": "Bus or journey date not found."}), 404
    occupied = booked_seats(bus_id, journey_date)
    all_seats = [f"{row}{col}" for row in range(1, 11) for col in ["A", "B", "C", "D"]]
    return jsonify({"bus": bus, "booked": sorted(occupied), "seats": all_seats[:bus["total_seats"]]})

@app.post("/api/bookings")
def create_booking():
    data = request.get_json(silent=True) or {}
    required = ["bus_id", "date", "name", "email", "phone", "seats"]
    if any(not data.get(k) for k in required):
        return jsonify({"error": "Please complete all passenger and seat details."}), 400
    bus = get_bus(int(data["bus_id"]))
    if not bus:
        return jsonify({"error": "Selected bus does not exist."}), 404
    journey_date = str(data["date"])
    if journey_date < date.today().isoformat():
        return jsonify({"error": "Journey date cannot be in the past."}), 400
    selected = list(dict.fromkeys(data["seats"]))
    if not selected or len(selected) > 6:
        return jsonify({"error": "Select between 1 and 6 seats."}), 400
    valid = {f"{r}{c}" for r in range(1, 11) for c in ["A", "B", "C", "D"]}
    if any(s not in valid for s in selected):
        return jsonify({"error": "Invalid seat selection."}), 400
    name, email, phone = str(data["name"]).strip(), str(data["email"]).strip(), str(data["phone"]).strip()
    if len(name) < 2 or "@" not in email or len(phone) < 8:
        return jsonify({"error": "Enter valid passenger details."}), 400
    ref = "BG" + "".join(secrets.choice(string.digits) for _ in range(8))
    total = len(selected) * bus["price"]
    try:
        with db() as conn:
            occupied = set()
            rows = conn.execute("SELECT seats FROM bookings WHERE bus_id=? AND journey_date=? AND status='CONFIRMED'", (bus["id"], journey_date)).fetchall()
            for row in rows:
                occupied.update(row["seats"].split(","))
            if occupied.intersection(selected):
                return jsonify({"error": "One or more selected seats were just booked. Please choose again."}), 409
            conn.execute("""INSERT INTO bookings
                (booking_ref,bus_id,origin,destination,journey_date,operator,bus_type,departure,arrival,
                passenger_name,email,phone,seats,total,status,created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (ref,bus["id"],bus["from"],bus["to"],journey_date,bus["operator"],bus["type"],bus["departure"],bus["arrival"],
                 name,email,phone,",".join(selected),total,"CONFIRMED",datetime.utcnow().isoformat()))
    except sqlite3.Error:
        return jsonify({"error": "Booking could not be saved. Please try again."}), 500
    return jsonify({"message": "Booking confirmed.", "booking": {
        "ref": ref, "name": name, "email": email, "origin": bus["from"], "destination": bus["to"],
        "date": journey_date, "operator": bus["operator"], "type": bus["type"],
        "departure": bus["departure"], "arrival": bus["arrival"], "seats": selected, "total": total
    }}), 201

@app.get("/api/bookings/<booking_ref>")
def lookup_booking(booking_ref):
    with db() as conn:
        row = conn.execute("SELECT * FROM bookings WHERE booking_ref=?", (booking_ref.upper(),)).fetchone()
    if not row:
        return jsonify({"error": "No booking found for that reference."}), 404
    booking = dict(row)
    booking["seats"] = booking["seats"].split(",")
    return jsonify({"booking": booking})

@app.get("/health")
def health():
    return jsonify({"status": "healthy", "service": "BusGo API"})

init_db()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5001)),
        debug=os.environ.get("FLASK_DEBUG") == "1"
    )
