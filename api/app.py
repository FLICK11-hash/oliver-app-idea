import os
import sqlite3
import uuid
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, jsonify, request
from flask_cors import CORS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "db")
DB_PATH = os.path.join(DB_DIR, "church_scheduler.sqlite3")

app = Flask(__name__)
CORS(app)

TOKENS = {}

ROLE_KIDS_TEACHER = "KIDS_TEACHER"
ROLE_KIDS_ASSISTANT = "KIDS_ASSISTANT"
ROLE_SETUP = "SETUP"
ROLE_COFFEE = "COFFEE"

ALL_ROLES = {
    ROLE_KIDS_TEACHER,
    ROLE_KIDS_ASSISTANT,
    ROLE_SETUP,
    ROLE_COFFEE,
}

def require_user():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header.replace("Bearer ", "", 1).strip()
    return TOKENS.get(token)

@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return jsonify({"error": "Username and password are required."}), 400

    conn = get_db()
    cur = conn.cursor()

    existing = cur.execute(
        "SELECT id FROM users WHERE username = ?",
        (username,)
    ).fetchone()

    if existing:
        conn.close()
        return jsonify({"error": "Username already exists."}), 400

    user_id = str(uuid.uuid4())
    password_hash = generate_password_hash(password)

    cur.execute(
        "INSERT INTO users (id, username, password_hash) VALUES (?, ?, ?)",
        (user_id, username, password_hash)
    )
    conn.commit()
    conn.close()

    token = str(uuid.uuid4())
    TOKENS[token] = user_id

    return jsonify({
        "token": token,
        "account": {
            "id": user_id,
            "username": username
        }
    }), 201

@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return jsonify({"error": "Username and password are required."}), 400

    conn = get_db()
    cur = conn.cursor()

    user = cur.execute(
        "SELECT id, username, password_hash FROM users WHERE username = ?",
        (username,)
    ).fetchone()

    conn.close()

    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid username or password."}), 401

    token = str(uuid.uuid4())
    TOKENS[token] = user["id"]

    return jsonify({
        "token": token,
        "account": {
            "id": user["id"],
            "username": user["username"]
        }
    })

def get_db() -> sqlite3.Connection:
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def previous_sunday(reference_date: date) -> date:
    days_since_sunday = (reference_date.weekday() + 1) % 7
    if days_since_sunday == 0:
        days_since_sunday = 7
    return reference_date - timedelta(days=days_since_sunday)


def same_month(d1: date, d2: date) -> bool:
    return d1.year == d2.year and d1.month == d2.month


def bool_from_request(data: Dict[str, Any], key: str, default: bool = False) -> bool:
    value = data.get(key, default)
    return bool(value)


def row_to_volunteer(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "name": row["name"],
        "gender": row["gender"],
        "active": bool(row["active"]),
        "archived": bool(row["archived"]),
        "phone": row["phone"],
        "email": row["email"],
        "canTeachKids": bool(row["can_teach_kids"]),
        "canAssistKids": bool(row["can_assist_kids"]),
        "canSetup": bool(row["can_setup"]),
        "canCoffee": bool(row["can_coffee"]),
        "kidsCoupleGroup": row["kids_couple_group"],
    }


def row_to_serve_record(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "date": row["date"],
        "volunteerId": row["volunteer_id"],
        "role": row["role"],
    }


def init_db() -> None:
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS members (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            gender TEXT NOT NULL CHECK (gender IN ('Male', 'Female')),
            active INTEGER NOT NULL DEFAULT 1,
            member_status TEXT,
            date_added TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS pastoral_prayer_records (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            date TEXT NOT NULL,
            member_id TEXT NOT NULL,
            gender TEXT NOT NULL CHECK (gender IN ('Male', 'Female')),
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (member_id) REFERENCES members (id)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS hymns (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            alternate_title TEXT,
            hymn_number TEXT,
            notes TEXT,
            active INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS hymn_usage_records (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            date TEXT NOT NULL,
            hymn_id TEXT NOT NULL,
            service_type TEXT,
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (hymn_id) REFERENCES hymns (id)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS volunteers (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            gender TEXT NOT NULL CHECK (gender IN ('Male', 'Female')),
            active INTEGER NOT NULL DEFAULT 1,
            archived INTEGER NOT NULL DEFAULT 0,
            phone TEXT,
            email TEXT,
            can_teach_kids INTEGER NOT NULL DEFAULT 0,
            can_assist_kids INTEGER NOT NULL DEFAULT 0,
            can_setup INTEGER NOT NULL DEFAULT 0,
            can_coffee INTEGER NOT NULL DEFAULT 0,
            kids_couple_group TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """
    )

    try:
        cur.execute("ALTER TABLE volunteers ADD COLUMN archived INTEGER NOT NULL DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        cur.execute("ALTER TABLE volunteers ADD COLUMN phone TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cur.execute("ALTER TABLE volunteers ADD COLUMN email TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cur.execute("ALTER TABLE volunteers ADD COLUMN user_id TEXT")
    except sqlite3.OperationalError:
        pass

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS serve_records (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            date TEXT NOT NULL,
            volunteer_id TEXT NOT NULL,
            role TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (volunteer_id) REFERENCES volunteers (id)
        )
        """
    )

    try:
        cur.execute("ALTER TABLE serve_records ADD COLUMN user_id TEXT")
    except sqlite3.OperationalError:
        pass

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS sunday_schedules (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            date TEXT NOT NULL,
            kids_teacher TEXT,
            coffee TEXT,
            UNIQUE(user_id, date),
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (kids_teacher) REFERENCES volunteers (id),
            FOREIGN KEY (coffee) REFERENCES volunteers (id)
        )
        """
    )

    try:
        cur.execute("ALTER TABLE sunday_schedules ADD COLUMN user_id TEXT")
    except sqlite3.OperationalError:
        pass

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS sunday_schedule_assignments (
            id TEXT PRIMARY KEY,
            schedule_id TEXT NOT NULL,
            assignment_group TEXT NOT NULL,
            volunteer_id TEXT NOT NULL,
            FOREIGN KEY (schedule_id) REFERENCES sunday_schedules (id),
            FOREIGN KEY (volunteer_id) REFERENCES volunteers (id)
        )
        """
    )

    conn.commit()
    conn.close()

def seed_if_empty() -> None:
    conn = get_db()
    cur = conn.cursor()

    existing = cur.execute("SELECT COUNT(*) AS count FROM volunteers").fetchone()["count"]
    if existing > 0:
        conn.close()
        return

    volunteers = [
        {
            "name": "Daniel",
            "gender": "Male",
            "active": 1,
            "archived": 0,
            "phone": None,
            "email": None,
            "can_teach_kids": 1,
            "can_assist_kids": 0,
            "can_setup": 1,
            "can_coffee": 1,
            "kids_couple_group": None,
        },
        {
            "name": "Mariam",
            "gender": "Female",
            "active": 1,
            "archived": 0,
            "phone": None,
            "email": None,
            "can_teach_kids": 1,
            "can_assist_kids": 1,
            "can_setup": 0,
            "can_coffee": 1,
            "kids_couple_group": "couple-a",
        },
        {
            "name": "John",
            "gender": "Male",
            "active": 1,
            "archived": 0,
            "phone": None,
            "email": None,
            "can_teach_kids": 0,
            "can_assist_kids": 1,
            "can_setup": 1,
            "can_coffee": 1,
            "kids_couple_group": "couple-a",
        },
        {
            "name": "Sarah",
            "gender": "Female",
            "active": 1,
            "archived": 0,
            "phone": None,
            "email": None,
            "can_teach_kids": 0,
            "can_assist_kids": 1,
            "can_setup": 0,
            "can_coffee": 1,
            "kids_couple_group": None,
        },
        {
            "name": "Michael",
            "gender": "Male",
            "active": 1,
            "archived": 0,
            "phone": None,
            "email": None,
            "can_teach_kids": 0,
            "can_assist_kids": 1,
            "can_setup": 1,
            "can_coffee": 0,
            "kids_couple_group": None,
        },
        {
            "name": "Rebecca",
            "gender": "Female",
            "active": 1,
            "archived": 0,
            "phone": None,
            "email": None,
            "can_teach_kids": 0,
            "can_assist_kids": 1,
            "can_setup": 0,
            "can_coffee": 1,
            "kids_couple_group": None,
        },
        {
            "name": "Peter",
            "gender": "Male",
            "active": 1,
            "archived": 0,
            "phone": None,
            "email": None,
            "can_teach_kids": 0,
            "can_assist_kids": 0,
            "can_setup": 1,
            "can_coffee": 0,
            "kids_couple_group": None,
        },
    ]

    volunteer_ids: List[str] = []
    for v in volunteers:
        volunteer_id = str(uuid.uuid4())
        volunteer_ids.append(volunteer_id)
        cur.execute(
            """
            INSERT INTO volunteers (
                id, name, gender, active, archived, phone, email,
                can_teach_kids, can_assist_kids, can_setup, can_coffee, kids_couple_group
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                volunteer_id,
                v["name"],
                v["gender"],
                v["active"],
                v["archived"],
                v["phone"],
                v["email"],
                v["can_teach_kids"],
                v["can_assist_kids"],
                v["can_setup"],
                v["can_coffee"],
                v["kids_couple_group"],
            ),
        )

    today = date.today()
    recent_sundays = [
        today - timedelta(days=today.weekday() + 1 + 7),
        today - timedelta(days=today.weekday() + 1 + 14),
        today - timedelta(days=today.weekday() + 1 + 21),
    ]

    sample_records = [
        (recent_sundays[0], volunteer_ids[0], ROLE_KIDS_TEACHER),
        (recent_sundays[0], volunteer_ids[3], ROLE_KIDS_ASSISTANT),
        (recent_sundays[0], volunteer_ids[4], ROLE_KIDS_ASSISTANT),
        (recent_sundays[0], volunteer_ids[2], ROLE_SETUP),
        (recent_sundays[0], volunteer_ids[6], ROLE_SETUP),
        (recent_sundays[0], volunteer_ids[1], ROLE_COFFEE),
        (recent_sundays[1], volunteer_ids[1], ROLE_KIDS_TEACHER),
        (recent_sundays[1], volunteer_ids[3], ROLE_KIDS_ASSISTANT),
        (recent_sundays[1], volunteer_ids[2], ROLE_KIDS_ASSISTANT),
        (recent_sundays[1], volunteer_ids[4], ROLE_SETUP),
        (recent_sundays[1], volunteer_ids[6], ROLE_SETUP),
        (recent_sundays[1], volunteer_ids[5], ROLE_COFFEE),
        (recent_sundays[2], volunteer_ids[0], ROLE_KIDS_TEACHER),
        (recent_sundays[2], volunteer_ids[5], ROLE_KIDS_ASSISTANT),
        (recent_sundays[2], volunteer_ids[2], ROLE_KIDS_ASSISTANT),
        (recent_sundays[2], volunteer_ids[4], ROLE_SETUP),
        (recent_sundays[2], volunteer_ids[6], ROLE_SETUP),
        (recent_sundays[2], volunteer_ids[3], ROLE_COFFEE),
    ]

    for record_date, volunteer_id, role in sample_records:
        cur.execute(
            """
            INSERT INTO serve_records (id, date, volunteer_id, role)
            VALUES (?, ?, ?, ?)
            """,
            (str(uuid.uuid4()), record_date.isoformat(), volunteer_id, role),
        )

    conn.commit()
    conn.close()

def row_to_member(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "name": row["name"],
        "gender": row["gender"],
        "active": bool(row["active"]),
        "memberStatus": row["member_status"],
        "dateAdded": row["date_added"],
    }


def row_to_pastoral_prayer_record(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "date": row["date"],
        "memberId": row["member_id"],
        "gender": row["gender"],
        "notes": row["notes"],
    }


def row_to_hymn(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "title": row["title"],
        "alternateTitle": row["alternate_title"],
        "hymnNumber": row["hymn_number"],
        "notes": row["notes"],
        "active": bool(row["active"]),
    }


def row_to_hymn_usage_record(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "date": row["date"],
        "hymnId": row["hymn_id"],
        "serviceType": row["service_type"],
        "notes": row["notes"],
    }

def get_all_members(user_id: str, active_only: bool = False) -> List[Dict[str, Any]]:
    conn = get_db()
    if active_only:
        rows = conn.execute(
            "SELECT * FROM members WHERE user_id = ? AND active = 1 ORDER BY name",
            (user_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM members WHERE user_id = ? ORDER BY name",
            (user_id,),
        ).fetchall()
    conn.close()
    return [row_to_member(row) for row in rows]

def get_prayer_records(user_id: str) -> List[Dict[str, Any]]:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM pastoral_prayer_records WHERE user_id = ? ORDER BY date DESC, gender ASC",
        (user_id,),
    ).fetchall()
    conn.close()
    return [row_to_pastoral_prayer_record(row) for row in rows]


def total_prayer_mentions(user_id: str, member_id: str) -> int:
    conn = get_db()
    row = conn.execute(
        "SELECT COUNT(*) AS count FROM pastoral_prayer_records WHERE user_id = ? AND member_id = ?",
        (user_id, member_id),
    ).fetchone()
    conn.close()
    return int(row["count"])


def last_prayed_for_date(user_id: str, member_id: str) -> Optional[date]:
    conn = get_db()
    row = conn.execute(
        """
        SELECT date FROM pastoral_prayer_records
        WHERE user_id = ? AND member_id = ?
        ORDER BY date DESC
        LIMIT 1
        """,
        (user_id, member_id),
    ).fetchone()
    conn.close()
    if row is None:
        return None
    return parse_date(row["date"])


def weeks_since_last_prayed_for(user_id: str, member_id: str, reference_date: date) -> int:
    last_date = last_prayed_for_date(user_id, member_id)
    if last_date is None:
        return 999
    delta_days = (reference_date - last_date).days
    if delta_days < 0:
        return 0
    return delta_days // 7

def get_top_prayer_candidates(user_id: str, gender: str, reference_date: date, n: int = 5) -> List[Dict[str, Any]]:
    members = [m for m in get_all_members(user_id, active_only=True) if m["gender"] == gender]
    if not members:
        return []

    total_counts = {m["id"]: total_prayer_mentions(user_id, m["id"]) for m in members}
    gaps = {m["id"]: weeks_since_last_prayed_for(user_id, m["id"], reference_date) for m in members}

    raw_scores: Dict[str, float] = {}

    for member in members:
        member_id = member["id"]
        total_count = total_counts[member_id]
        gap = gaps[member_id]

        date_added = parse_date(member["dateAdded"])
        is_new = (reference_date - date_added).days <= 14
        never_prayed = total_count == 0

        gap_value = 50 if gap == 999 else gap

        raw = 0.0
        raw += 100.0 if never_prayed else 0.0
        raw += 40.0 if is_new else 0.0
        raw += gap_value * 2.0
        raw += max(0, 10 - total_count) * 3.0

        raw_scores[member_id] = raw

    results = []
    for member in members:
        member_id = member["id"]
        last_date = last_prayed_for_date(user_id, member_id)
        results.append({
            "member": member,
            "priority": round(raw_scores[member_id], 2),
            "stats": {
                "totalPrayerMentions": total_counts[member_id],
                "lastPrayedForDate": last_date.isoformat() if last_date else None,
                "weeksSinceLastPrayedFor": None if gaps[member_id] == 999 else gaps[member_id],
                "neverPrayedFor": total_counts[member_id] == 0,
            }
        })

    results.sort(key=lambda x: (-x["priority"], x["member"]["name"]))
    return results[:n]

def get_all_volunteers(user_id: str, include_archived: bool = True) -> List[Dict[str, Any]]:
    conn = get_db()
    if include_archived:
        rows = conn.execute(
            "SELECT * FROM volunteers WHERE user_id = ? ORDER BY name",
            (user_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM volunteers WHERE user_id = ? AND archived = 0 ORDER BY name",
            (user_id,),
        ).fetchall()
    conn.close()
    return [row_to_volunteer(row) for row in rows]

def get_volunteer_map(user_id: str) -> Dict[str, Dict[str, Any]]:
    volunteers = get_all_volunteers(user_id, include_archived=True)
    return {v["id"]: v for v in volunteers}

def get_serve_records(user_id: str) -> List[Dict[str, Any]]:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM serve_records WHERE user_id = ? ORDER BY date DESC, role ASC",
        (user_id,),
    ).fetchall()
    conn.close()
    return [row_to_serve_record(row) for row in rows]

def get_records_for_volunteer(user_id: str, volunteer_id: str) -> List[Dict[str, Any]]:
    conn = get_db()
    rows = conn.execute(
        """
        SELECT * FROM serve_records
        WHERE user_id = ? AND volunteer_id = ?
        ORDER BY date DESC
        """,
        (user_id, volunteer_id),
    ).fetchall()
    conn.close()
    return [row_to_serve_record(row) for row in rows]

def total_serves(user_id: str, volunteer_id: str) -> int:
    conn = get_db()
    row = conn.execute(
        "SELECT COUNT(*) AS count FROM serve_records WHERE user_id = ? AND volunteer_id = ?",
        (user_id, volunteer_id),
    ).fetchone()
    conn.close()
    return int(row["count"])

def serves_this_month(user_id: str, volunteer_id: str, reference_date: date) -> int:
    conn = get_db()
    rows = conn.execute(
        "SELECT date FROM serve_records WHERE user_id = ? AND volunteer_id = ?",
        (user_id, volunteer_id),
    ).fetchall()
    conn.close()

    count = 0
    for row in rows:
        served_date = parse_date(row["date"])
        if same_month(served_date, reference_date):
            count += 1
    return count

def last_served_date(user_id: str, volunteer_id: str) -> Optional[date]:
    conn = get_db()
    row = conn.execute(
        """
        SELECT date FROM serve_records
        WHERE user_id = ? AND volunteer_id = ?
        ORDER BY date DESC
        LIMIT 1
        """,
        (user_id, volunteer_id),
    ).fetchone()
    conn.close()

    if row is None:
        return None
    return parse_date(row["date"])

def sundays_since_last_served(user_id: str, volunteer_id: str, reference_date: date) -> int:
    last_date = last_served_date(user_id, volunteer_id)
    if last_date is None:
        return 999

    delta_days = (reference_date - last_date).days
    if delta_days < 0:
        return 0
    return delta_days // 7

def served_last_sunday(user_id: str, volunteer_id: str, reference_date: date) -> bool:
    target = previous_sunday(reference_date).isoformat()
    conn = get_db()
    row = conn.execute(
        """
        SELECT 1 FROM serve_records
        WHERE user_id = ? AND volunteer_id = ? AND date = ?
        LIMIT 1
        """,
        (user_id, volunteer_id, target),
    ).fetchone()
    conn.close()
    return row is not None

def is_eligible_for_role(volunteer: Dict[str, Any], role: str) -> bool:
    if not volunteer["active"] or volunteer["archived"]:
        return False

    if role == ROLE_KIDS_TEACHER:
        return volunteer["canTeachKids"]
    if role == ROLE_KIDS_ASSISTANT:
        return volunteer["canAssistKids"]
    if role == ROLE_SETUP:
        return volunteer["canSetup"] and volunteer["gender"] == "Male"
    if role == ROLE_COFFEE:
        return volunteer["canCoffee"]

    return False

def eligible_volunteers_for_role(user_id: str, role: str) -> List[Dict[str, Any]]:
    volunteers = get_all_volunteers(user_id, include_archived=False)
    return [v for v in volunteers if is_eligible_for_role(v, role)]

def compute_priority_scores(user_id: str, role: str, reference_date: date) -> List[Dict[str, Any]]:
    volunteers = eligible_volunteers_for_role(user_id, role)
    if not volunteers:
        return []

    total_counts = {v["id"]: total_serves(user_id, v["id"]) for v in volunteers}
    monthly_counts = {v["id"]: serves_this_month(user_id, v["id"], reference_date) for v in volunteers}
    sunday_gaps = {v["id"]: sundays_since_last_served(user_id, v["id"], reference_date) for v in volunteers}
    last_sunday_flags = {v["id"]: served_last_sunday(user_id, v["id"], reference_date) for v in volunteers}

    finite_gaps = [gap for gap in sunday_gaps.values() if gap != 999]
    max_gap = max(finite_gaps) if finite_gaps else 0
    max_total = max(total_counts.values()) if total_counts else 0
    max_month = max(monthly_counts.values()) if monthly_counts else 0

    raw_scores: Dict[str, float] = {}

    for volunteer in volunteers:
        volunteer_id = volunteer["id"]
        total_count = total_counts[volunteer_id]
        month_count = monthly_counts[volunteer_id]
        gap = sunday_gaps[volunteer_id]
        served_recently = last_sunday_flags[volunteer_id]

        gap_value = (max_gap + 2) if gap == 999 else gap
        raw = 0.0
        raw += gap_value * 2.0
        raw += (max_total - total_count) * 3.0
        raw += (max_month - month_count) * 4.0
        raw -= 8.0 if served_recently else 0.0
        raw += 20.0 if total_count == 0 else 0.0

        raw_scores[volunteer_id] = raw

    min_raw = min(raw_scores.values())
    max_raw = max(raw_scores.values())

    results = []
    for volunteer in volunteers:
        volunteer_id = volunteer["id"]
        raw = raw_scores[volunteer_id]
        volunteer_last_served = last_served_date(user_id, volunteer_id)

        if max_raw == min_raw:
            priority = 100
        else:
            priority = round(1 + 99 * (raw - min_raw) / (max_raw - min_raw))

        results.append(
            {
                "volunteer": volunteer,
                "role": role,
                "priority": int(priority),
                "rawScore": round(raw, 2),
                "stats": {
                    "totalServes": total_counts[volunteer_id],
                    "servesThisMonth": monthly_counts[volunteer_id],
                    "lastServedDate": (
                        volunteer_last_served.isoformat()
                        if volunteer_last_served is not None
                        else None
                    ),
                    "sundaysSinceLastServed": (
                        None if sunday_gaps[volunteer_id] == 999 else sunday_gaps[volunteer_id]
                    ),
                    "servedLastSunday": last_sunday_flags[volunteer_id],
                    "neverServed": total_counts[volunteer_id] == 0,
                },
            }
        )

    results.sort(key=lambda item: (-item["priority"], item["volunteer"]["name"]))
    return results

def get_top_candidates(user_id: str, role: str, reference_date: date, n: int = 5) -> List[Dict[str, Any]]:
    return compute_priority_scores(user_id, role, reference_date)[:n]

def load_schedule_by_date(user_id: str, schedule_date: str) -> Optional[Dict[str, Any]]:
    conn = get_db()
    schedule_row = conn.execute(
        "SELECT * FROM sunday_schedules WHERE user_id = ? AND date = ?",
        (user_id, schedule_date),
    ).fetchone()

    if schedule_row is None:
        conn.close()
        return None

    assignment_rows = conn.execute(
        """
        SELECT assignment_group, volunteer_id
        FROM sunday_schedule_assignments
        WHERE schedule_id = ?
        ORDER BY assignment_group, id
        """,
        (schedule_row["id"],),
    ).fetchall()
    conn.close()

    kids_assistants: List[str] = []
    setup: List[str] = []

    for row in assignment_rows:
        if row["assignment_group"] == "kidsAssistants":
            kids_assistants.append(row["volunteer_id"])
        elif row["assignment_group"] == "setup":
            setup.append(row["volunteer_id"])

    return {
        "date": schedule_row["date"],
        "kidsTeacher": schedule_row["kids_teacher"],
        "kidsAssistants": kids_assistants,
        "setup": setup,
        "coffee": schedule_row["coffee"],
    }

def validate_schedule(user_id: str, schedule: Dict[str, Any]) -> Dict[str, List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    volunteer_map = get_volunteer_map(user_id)
    schedule_date = parse_date(schedule["date"])

    kids_teacher = schedule.get("kidsTeacher")
    kids_assistants = schedule.get("kidsAssistants", [])
    setup = schedule.get("setup", [])
    coffee = schedule.get("coffee")

    if not kids_teacher:
        errors.append("Kids must have exactly 1 teacher.")
    if len(kids_assistants) != 2:
        errors.append("Kids must have exactly 2 assistants.")
    if len(setup) != 2:
        errors.append("Setup must have exactly 2 people.")
    if not coffee:
        errors.append("Coffee must have exactly 1 volunteer.")

    assigned_ids: List[str] = []
    if kids_teacher:
        assigned_ids.append(kids_teacher)
    assigned_ids.extend(kids_assistants)
    assigned_ids.extend(setup)
    if coffee:
        assigned_ids.append(coffee)

    if len(assigned_ids) != len(set(assigned_ids)):
        errors.append("A volunteer cannot be assigned more than once on the same Sunday.")

    kids_group_ids: List[str] = []
    if kids_teacher:
        kids_group_ids.append(kids_teacher)
    kids_group_ids.extend(kids_assistants)

    if len(kids_group_ids) == 3:
        female_count = 0
        couple_groups = []

        for volunteer_id in kids_group_ids:
            volunteer = volunteer_map.get(volunteer_id)
            if volunteer is None:
                errors.append(f"Unknown volunteer in kids room: {volunteer_id}")
                continue

            if volunteer["gender"] == "Female":
                female_count += 1

            if volunteer["kidsCoupleGroup"]:
                couple_groups.append(volunteer["kidsCoupleGroup"])

        if female_count < 1:
            errors.append("Kids room must include at least 1 female.")

        if len(couple_groups) != len(set(couple_groups)):
            errors.append("Married couples cannot serve together in the kids room.")

    if kids_teacher:
        volunteer = volunteer_map.get(kids_teacher)
        if volunteer is None or not is_eligible_for_role(volunteer, ROLE_KIDS_TEACHER):
            errors.append("Kids teacher is not eligible for that role.")

    for volunteer_id in kids_assistants:
        volunteer = volunteer_map.get(volunteer_id)
        if volunteer is None or not is_eligible_for_role(volunteer, ROLE_KIDS_ASSISTANT):
            errors.append(f"Kids assistant is not eligible: {volunteer_id}")

    for volunteer_id in setup:
        volunteer = volunteer_map.get(volunteer_id)
        if volunteer is None:
            errors.append(f"Unknown setup volunteer: {volunteer_id}")
            continue
        if volunteer["gender"] != "Male":
            errors.append("Both setup volunteers must be male.")
        if not is_eligible_for_role(volunteer, ROLE_SETUP):
            errors.append(f"Setup volunteer is not eligible: {volunteer['name']}")

    if coffee:
        volunteer = volunteer_map.get(coffee)
        if volunteer is None or not is_eligible_for_role(volunteer, ROLE_COFFEE):
            errors.append("Coffee volunteer is not eligible for that role.")

    for volunteer_id in assigned_ids:
        volunteer = volunteer_map.get(volunteer_id)
        if volunteer is None:
            continue

        if served_last_sunday(user_id, volunteer_id, schedule_date):
            warnings.append(f"{volunteer['name']} served last Sunday.")

        if serves_this_month(user_id, volunteer_id, schedule_date) > 0:
            warnings.append(f"{volunteer['name']} has already served this month.")

        if total_serves(user_id, volunteer_id) >= 5:
            warnings.append(f"{volunteer['name']} has a relatively high total serve count.")

    return {
        "errors": sorted(list(set(errors))),
        "warnings": sorted(list(set(warnings))),
    }

def dashboard_stats(user_id: str, reference_date: date) -> Dict[str, Any]:
    volunteers = get_all_volunteers(user_id, include_archived=True)
    active_count = len([v for v in volunteers if v["active"] and not v["archived"]])
    records = get_serve_records(user_id)

    return {
        "totalVolunteers": len(volunteers),
        "activeVolunteers": active_count,
        "totalServeRecords": len(records),
        "topCandidates": {
            ROLE_KIDS_TEACHER: get_top_candidates(user_id, ROLE_KIDS_TEACHER, reference_date, 5),
            ROLE_KIDS_ASSISTANT: get_top_candidates(user_id, ROLE_KIDS_ASSISTANT, reference_date, 5),
            ROLE_SETUP: get_top_candidates(user_id, ROLE_SETUP, reference_date, 5),
            ROLE_COFFEE: get_top_candidates(user_id, ROLE_COFFEE, reference_date, 5),
        },
    }

@app.route("/api/members", methods=["GET"])
def list_members() -> Any:
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    active_only = request.args.get("activeOnly", "false").lower() == "true"
    return jsonify(get_all_members(user_id, active_only=active_only))


@app.route("/api/members", methods=["POST"])
def create_member() -> Any:
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    gender = data.get("gender")
    active = 1 if data.get("active", True) else 0
    member_status = (data.get("memberStatus") or "").strip() or None
    date_added = (data.get("dateAdded") or date.today().isoformat())

    if not name:
        return jsonify({"error": "Name is required."}), 400
    if gender not in ("Male", "Female"):
        return jsonify({"error": "Gender must be Male or Female."}), 400

    member_id = str(uuid.uuid4())
    conn = get_db()
    conn.execute(
        """
        INSERT INTO members (id, user_id, name, gender, active, member_status, date_added)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (member_id, user_id, name, gender, active, member_status, date_added),
    )
    conn.commit()
    conn.close()

    return jsonify({"ok": True, "id": member_id}), 201

@app.route("/api/pastoral-prayer-records", methods=["GET"])
def list_pastoral_prayer_records() -> Any:
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    return jsonify(get_prayer_records(user_id))


@app.route("/api/pastoral-prayer-records", methods=["POST"])
def create_pastoral_prayer_records() -> Any:
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    record_date = data.get("date")
    male_member_id = data.get("maleMemberId")
    female_member_id = data.get("femaleMemberId")
    notes = (data.get("notes") or "").strip() or None

    if not record_date or not male_member_id or not female_member_id:
        return jsonify({"error": "date, maleMemberId, and femaleMemberId are required."}), 400

    conn = get_db()

    male_row = conn.execute(
        "SELECT * FROM members WHERE id = ? AND user_id = ?",
        (male_member_id, user_id),
    ).fetchone()

    female_row = conn.execute(
        "SELECT * FROM members WHERE id = ? AND user_id = ?",
        (female_member_id, user_id),
    ).fetchone()

    if male_row is None or female_row is None:
        conn.close()
        return jsonify({"error": "Member not found."}), 404

    if male_row["gender"] != "Male" or female_row["gender"] != "Female":
        conn.close()
        return jsonify({"error": "Pastoral prayer must include 1 male and 1 female."}), 400

    conn.execute(
        """
        INSERT INTO pastoral_prayer_records (id, user_id, date, member_id, gender, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (str(uuid.uuid4()), user_id, record_date, male_member_id, "Male", notes),
    )

    conn.execute(
        """
        INSERT INTO pastoral_prayer_records (id, user_id, date, member_id, gender, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (str(uuid.uuid4()), user_id, record_date, female_member_id, "Female", notes),
    )

    conn.commit()
    conn.close()

    return jsonify({"ok": True})

@app.route("/api/pastoral-prayer-suggestions", methods=["GET"])
def pastoral_prayer_suggestions() -> Any:
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    reference_date_str = request.args.get("date")
    reference_date = parse_date(reference_date_str) if reference_date_str else date.today()

    return jsonify({
        "male": get_top_prayer_candidates(user_id, "Male", reference_date, 5),
        "female": get_top_prayer_candidates(user_id, "Female", reference_date, 5),
    })

@app.route("/api/health", methods=["GET"])
def health() -> Any:
    return jsonify({"ok": True})

@app.route("/api/dashboard", methods=["GET"])
def get_dashboard() -> Any:
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    reference_date_str = request.args.get("date")
    reference_date = parse_date(reference_date_str) if reference_date_str else date.today()
    return jsonify(dashboard_stats(user_id, reference_date))


@app.route("/api/volunteers", methods=["GET"])
def list_volunteers() -> Any:
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    include_archived = request.args.get("includeArchived", "true").lower() == "true"
    return jsonify(get_all_volunteers(user_id, include_archived=include_archived))

@app.route("/api/volunteers", methods=["POST"])
def create_volunteer():
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}

    volunteer_id = str(uuid.uuid4())
    name = (data.get("name") or "").strip()
    gender = data.get("gender") or "Male"
    active = 1 if data.get("active", True) else 0
    archived = 1 if data.get("archived", False) else 0
    phone = (data.get("phone") or "").strip() or None
    email = (data.get("email") or "").strip() or None
    can_teach_kids = 1 if data.get("canTeachKids", False) else 0
    can_assist_kids = 1 if data.get("canAssistKids", False) else 0
    can_setup = 1 if data.get("canSetup", False) else 0
    can_coffee = 1 if data.get("canCoffee", False) else 0
    kids_couple_group = (data.get("kidsCoupleGroup") or "").strip() or None

    if not name:
        return jsonify({"error": "Name is required"}), 400

    conn = get_db()
    try:
        conn.execute(
            """
            INSERT INTO volunteers (
                id, user_id, name, gender, active, archived, phone, email,
                can_teach_kids, can_assist_kids, can_setup, can_coffee, kids_couple_group
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                volunteer_id,
                user_id,
                name,
                gender,
                active,
                archived,
                phone,
                email,
                can_teach_kids,
                can_assist_kids,
                can_setup,
                can_coffee,
                kids_couple_group,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return jsonify({"ok": True, "id": volunteer_id}), 201

@app.route("/api/volunteers/<volunteer_id>", methods=["PUT"])
def update_volunteer(volunteer_id: str) -> Any:
    data = request.get_json(force=True)
    name = (data.get("name") or "").strip()
    gender = data.get("gender")
    kids_couple_group = data.get("kidsCoupleGroup")

    if not name:
        return jsonify({"error": "Name is required."}), 400
    if gender not in ("Male", "Female"):
        return jsonify({"error": "Gender must be Male or Female."}), 400

    conn = get_db()
    existing = conn.execute(
        "SELECT id FROM volunteers WHERE id = ?",
        (volunteer_id,),
    ).fetchone()

    if existing is None:
        conn.close()
        return jsonify({"error": "Volunteer not found."}), 404

    new_active = 1 if bool_from_request(data, "active", True) else 0
    new_archived = 0 if new_active == 1 else 1 if bool_from_request(data, "archived", False) else 0

    conn.execute(
        """
        UPDATE volunteers
        SET name = ?, gender = ?, active = ?, archived = ?,
            phone = ?, email = ?,
            can_teach_kids = ?, can_assist_kids = ?, can_setup = ?, can_coffee = ?,
            kids_couple_group = ?
        WHERE id = ?
        """,
        (
            name,
            gender,
            new_active,
            new_archived,
            (data.get("phone") or "").strip() or None,
            (data.get("email") or "").strip() or None,
            1 if bool_from_request(data, "canTeachKids") else 0,
            1 if bool_from_request(data, "canAssistKids") else 0,
            1 if bool_from_request(data, "canSetup") else 0,
            1 if bool_from_request(data, "canCoffee") else 0,
            kids_couple_group if kids_couple_group else None,
            volunteer_id,
        ),
    )
    conn.commit()
    conn.close()

    volunteer = next(v for v in get_all_volunteers(include_archived=True) if v["id"] == volunteer_id)
    return jsonify(volunteer)


@app.route("/api/volunteers/<volunteer_id>", methods=["DELETE"])
def delete_volunteer(volunteer_id: str) -> Any:
    conn = get_db()

    existing = conn.execute(
        "SELECT id FROM volunteers WHERE id = ?",
        (volunteer_id,),
    ).fetchone()

    if existing is None:
        conn.close()
        return jsonify({"error": "Volunteer not found."}), 404

    conn.execute(
        """
        UPDATE volunteers
        SET active = 0, archived = 1
        WHERE id = ?
        """,
        (volunteer_id,),
    )
    conn.commit()
    conn.close()

    return jsonify({"ok": True, "message": "Volunteer archived."})


@app.route("/api/serve-records", methods=["GET"])
def list_serve_records() -> Any:
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM serve_records WHERE user_id = ? ORDER BY date DESC, role ASC",
        (user_id,),
    ).fetchall()
    conn.close()

    return jsonify([row_to_serve_record(row) for row in rows])


@app.route("/api/serve-records", methods=["POST"])
def create_serve_record() -> Any:
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(force=True)

    record_date = data.get("date")
    volunteer_id = data.get("volunteerId")
    role = data.get("role")

    if not record_date or not volunteer_id or not role:
        return jsonify({"error": "date, volunteerId, and role are required."}), 400

    if role not in ALL_ROLES:
        return jsonify({"error": "Invalid role."}), 400

    conn = get_db()
    volunteer_row = conn.execute(
        "SELECT * FROM volunteers WHERE id = ? AND user_id = ?",
        (volunteer_id, user_id),
    ).fetchone()

    if volunteer_row is None:
        conn.close()
        return jsonify({"error": "Volunteer not found."}), 404

    volunteer = row_to_volunteer(volunteer_row)

    if not is_eligible_for_role(volunteer, role):
        conn.close()
        return jsonify({"error": "Volunteer is not eligible for that role."}), 400

    record_day = parse_date(record_date)
    if record_day.weekday() != 6:
        conn.close()
        return jsonify({"error": "Serve record date must be a Sunday."}), 400

    record_id = str(uuid.uuid4())
    conn.execute(
        """
        INSERT INTO serve_records (id, user_id, date, volunteer_id, role)
        VALUES (?, ?, ?, ?, ?)
        """,
        (record_id, user_id, record_date, volunteer_id, role),
    )
    conn.commit()
    conn.close()

    return jsonify(
        {
            "id": record_id,
            "date": record_date,
            "volunteerId": volunteer_id,
            "role": role,
        }
    ), 201


@app.route("/api/serve-records/<record_id>", methods=["DELETE"])
def delete_serve_record(record_id: str) -> Any:
    conn = get_db()

    existing = conn.execute(
        "SELECT id FROM serve_records WHERE id = ?",
        (record_id,),
    ).fetchone()

    if existing is None:
        conn.close()
        return jsonify({"error": "Serve record not found."}), 404

    conn.execute("DELETE FROM serve_records WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()

    return jsonify({"ok": True})

@app.route("/api/suggestions/<role>", methods=["GET"])
def suggestions(role: str) -> Any:
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    if role not in ALL_ROLES:
        return jsonify({"error": "Invalid role."}), 400

    reference_date_str = request.args.get("date")
    reference_date = parse_date(reference_date_str) if reference_date_str else date.today()
    limit = int(request.args.get("limit", "5"))

    return jsonify(get_top_candidates(user_id, role, reference_date, limit))

@app.route("/api/schedules/<schedule_date>", methods=["GET"])
def get_schedule(schedule_date: str) -> Any:
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    parse_date(schedule_date)
    schedule = load_schedule_by_date(user_id, schedule_date)
    if schedule is None:
        return jsonify(
            {
                "date": schedule_date,
                "kidsTeacher": None,
                "kidsAssistants": [],
                "setup": [],
                "coffee": None,
            }
        )
    return jsonify(schedule)

@app.route("/api/schedules/<schedule_date>", methods=["PUT"])
def save_schedule(schedule_date: str) -> Any:
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    schedule_day = parse_date(schedule_date)
    if schedule_day.weekday() != 6:
        return jsonify({"error": "Schedule date must be a Sunday."}), 400

    data = request.get_json(force=True)

    schedule = {
        "date": schedule_date,
        "kidsTeacher": data.get("kidsTeacher"),
        "kidsAssistants": data.get("kidsAssistants", []),
        "setup": data.get("setup", []),
        "coffee": data.get("coffee"),
    }

    validation = validate_schedule(user_id, schedule)

    conn = get_db()
    cur = conn.cursor()

    existing = cur.execute(
        "SELECT id FROM sunday_schedules WHERE user_id = ? AND date = ?",
        (user_id, schedule_date),
    ).fetchone()

    schedule_id = existing["id"] if existing else str(uuid.uuid4())

    if existing:
        cur.execute(
            """
            UPDATE sunday_schedules
            SET kids_teacher = ?, coffee = ?
            WHERE id = ?
            """,
            (schedule["kidsTeacher"], schedule["coffee"], schedule_id),
        )
        cur.execute(
            "DELETE FROM sunday_schedule_assignments WHERE schedule_id = ?",
            (schedule_id,),
        )
    else:
        cur.execute(
            """
            INSERT INTO sunday_schedules (id, user_id, date, kids_teacher, coffee)
            VALUES (?, ?, ?, ?, ?)
            """,
            (schedule_id, user_id, schedule_date, schedule["kidsTeacher"], schedule["coffee"]),
        )

    for volunteer_id in schedule["kidsAssistants"]:
        cur.execute(
            """
            INSERT INTO sunday_schedule_assignments (id, schedule_id, assignment_group, volunteer_id)
            VALUES (?, ?, ?, ?)
            """,
            (str(uuid.uuid4()), schedule_id, "kidsAssistants", volunteer_id),
        )

    for volunteer_id in schedule["setup"]:
        cur.execute(
            """
            INSERT INTO sunday_schedule_assignments (id, schedule_id, assignment_group, volunteer_id)
            VALUES (?, ?, ?, ?)
            """,
            (str(uuid.uuid4()), schedule_id, "setup", volunteer_id),
        )

    cur.execute(
        "DELETE FROM serve_records WHERE user_id = ? AND date = ?",
        (user_id, schedule_date),
    )

    if schedule["kidsTeacher"]:
        cur.execute(
            """
            INSERT INTO serve_records (id, user_id, date, volunteer_id, role)
            VALUES (?, ?, ?, ?, ?)
            """,
            (str(uuid.uuid4()), user_id, schedule_date, schedule["kidsTeacher"], ROLE_KIDS_TEACHER),
        )

    for volunteer_id in schedule["kidsAssistants"]:
        cur.execute(
            """
            INSERT INTO serve_records (id, user_id, date, volunteer_id, role)
            VALUES (?, ?, ?, ?, ?)
            """,
            (str(uuid.uuid4()), user_id, schedule_date, volunteer_id, ROLE_KIDS_ASSISTANT),
        )

    for volunteer_id in schedule["setup"]:
        cur.execute(
            """
            INSERT INTO serve_records (id, user_id, date, volunteer_id, role)
            VALUES (?, ?, ?, ?, ?)
            """,
            (str(uuid.uuid4()), user_id, schedule_date, volunteer_id, ROLE_SETUP),
        )

    if schedule["coffee"]:
        cur.execute(
            """
            INSERT INTO serve_records (id, user_id, date, volunteer_id, role)
            VALUES (?, ?, ?, ?, ?)
            """,
            (str(uuid.uuid4()), user_id, schedule_date, schedule["coffee"], ROLE_COFFEE),
        )

    conn.commit()
    conn.close()

    return jsonify(
        {
            "schedule": schedule,
            "validation": validation,
            "message": "Schedule saved successfully.",
        }
    )

@app.route("/api/validate-schedule", methods=["POST"])
def validate_schedule_route() -> Any:
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(force=True)

    schedule = {
        "date": data.get("date"),
        "kidsTeacher": data.get("kidsTeacher"),
        "kidsAssistants": data.get("kidsAssistants", []),
        "setup": data.get("setup", []),
        "coffee": data.get("coffee"),
    }

    if not schedule["date"]:
        return jsonify({"error": "date is required."}), 400

    schedule_day = parse_date(schedule["date"])
    if schedule_day.weekday() != 6:
        return jsonify(
            {
                "errors": ["Schedule date must be a Sunday."],
                "warnings": [],
            }
        )

    return jsonify(validate_schedule(user_id, schedule))

@app.route("/api/stats/volunteer/<volunteer_id>", methods=["GET"])
def volunteer_stats(volunteer_id: str) -> Any:
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    volunteer_map = get_volunteer_map(user_id)
    volunteer = volunteer_map.get(volunteer_id)
    if volunteer is None:
        return jsonify({"error": "Volunteer not found."}), 404

    reference_date_str = request.args.get("date")
    reference_date = parse_date(reference_date_str) if reference_date_str else date.today()

    volunteer_last_served = last_served_date(user_id, volunteer_id)

    return jsonify(
        {
            "volunteer": volunteer,
            "totalServes": total_serves(user_id, volunteer_id),
            "servesThisMonth": serves_this_month(user_id, volunteer_id, reference_date),
            "lastServedDate": (
                volunteer_last_served.isoformat()
                if volunteer_last_served is not None
                else None
            ),
            "sundaysSinceLastServed": sundays_since_last_served(user_id, volunteer_id, reference_date),
            "servedLastSunday": served_last_sunday(user_id, volunteer_id, reference_date),
            "history": get_records_for_volunteer(user_id, volunteer_id),
        }
    )

def get_all_hymns(user_id: str, active_only: bool = False) -> List[Dict[str, Any]]:
    conn = get_db()
    if active_only:
        rows = conn.execute(
            "SELECT * FROM hymns WHERE user_id = ? AND active = 1 ORDER BY title",
            (user_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM hymns WHERE user_id = ? ORDER BY title",
            (user_id,),
        ).fetchall()
    conn.close()
    return [row_to_hymn(row) for row in rows]


def get_hymn_usage_records(user_id: str) -> List[Dict[str, Any]]:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM hymn_usage_records WHERE user_id = ? ORDER BY date DESC",
        (user_id,),
    ).fetchall()
    conn.close()
    return [row_to_hymn_usage_record(row) for row in rows]


def total_times_sung(user_id: str, hymn_id: str) -> int:
    conn = get_db()
    row = conn.execute(
        "SELECT COUNT(*) AS count FROM hymn_usage_records WHERE user_id = ? AND hymn_id = ?",
        (user_id, hymn_id),
    ).fetchone()
    conn.close()
    return int(row["count"])


def last_sung_date(user_id: str, hymn_id: str) -> Optional[date]:
    conn = get_db()
    row = conn.execute(
        """
        SELECT date FROM hymn_usage_records
        WHERE user_id = ? AND hymn_id = ?
        ORDER BY date DESC
        LIMIT 1
        """,
        (user_id, hymn_id),
    ).fetchone()
    conn.close()
    if row is None:
        return None
    return parse_date(row["date"])


def weeks_since_last_sung(user_id: str, hymn_id: str, reference_date: date) -> Optional[int]:
    last_date = last_sung_date(user_id, hymn_id)
    if last_date is None:
        return None
    delta_days = (reference_date - last_date).days
    if delta_days < 0:
        return 0
    return delta_days // 7

@app.route("/api/hymns", methods=["GET"])
def list_hymns() -> Any:
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    active_only = request.args.get("activeOnly", "false").lower() == "true"
    return jsonify(get_all_hymns(user_id, active_only=active_only))


@app.route("/api/hymns", methods=["POST"])
def create_hymn() -> Any:
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    title = (data.get("title") or "").strip()
    alternate_title = (data.get("alternateTitle") or "").strip() or None
    hymn_number = (data.get("hymnNumber") or "").strip() or None
    notes = (data.get("notes") or "").strip() or None
    active = 1 if data.get("active", True) else 0

    if not title:
        return jsonify({"error": "Title is required."}), 400

    hymn_id = str(uuid.uuid4())
    conn = get_db()
    conn.execute(
        """
        INSERT INTO hymns (id, user_id, title, alternate_title, hymn_number, notes, active)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (hymn_id, user_id, title, alternate_title, hymn_number, notes, active),
    )
    conn.commit()
    conn.close()

    return jsonify({"ok": True, "id": hymn_id}), 201


@app.route("/api/hymn-usage-records", methods=["GET"])
def list_hymn_usage_records() -> Any:
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    return jsonify(get_hymn_usage_records(user_id))


@app.route("/api/hymn-usage-records", methods=["POST"])
def create_hymn_usage_record() -> Any:
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    record_date = data.get("date")
    hymn_id = data.get("hymnId")
    service_type = (data.get("serviceType") or "").strip() or None
    notes = (data.get("notes") or "").strip() or None

    if not record_date or not hymn_id:
        return jsonify({"error": "date and hymnId are required."}), 400

    conn = get_db()
    hymn_row = conn.execute(
        "SELECT id FROM hymns WHERE id = ? AND user_id = ?",
        (hymn_id, user_id),
    ).fetchone()

    if hymn_row is None:
        conn.close()
        return jsonify({"error": "Hymn not found."}), 404

    record_id = str(uuid.uuid4())
    conn.execute(
        """
        INSERT INTO hymn_usage_records (id, user_id, date, hymn_id, service_type, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (record_id, user_id, record_date, hymn_id, service_type, notes),
    )
    conn.commit()
    conn.close()

    return jsonify({"ok": True, "id": record_id}), 201

@app.route("/api/pastoral-prayer-records/<record_id>", methods=["DELETE"])
def delete_pastoral_prayer_record(record_id: str) -> Any:
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db()

    existing = conn.execute(
        "SELECT id FROM pastoral_prayer_records WHERE id = ? AND user_id = ?",
        (record_id, user_id),
    ).fetchone()

    if existing is None:
        conn.close()
        return jsonify({"error": "Pastoral prayer record not found."}), 404

    conn.execute(
        "DELETE FROM pastoral_prayer_records WHERE id = ? AND user_id = ?",
        (record_id, user_id),
    )
    conn.commit()
    conn.close()

    return jsonify({"ok": True})

@app.route("/api/hymns/<hymn_id>", methods=["DELETE"])
def delete_hymn(hymn_id: str) -> Any:
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db()

    existing = conn.execute(
        "SELECT id FROM hymns WHERE id = ? AND user_id = ?",
        (hymn_id, user_id),
    ).fetchone()

    if existing is None:
        conn.close()
        return jsonify({"error": "Hymn not found."}), 404

    conn.execute(
        "DELETE FROM hymn_usage_records WHERE hymn_id = ? AND user_id = ?",
        (hymn_id, user_id),
    )
    conn.execute(
        "DELETE FROM hymns WHERE id = ? AND user_id = ?",
        (hymn_id, user_id),
    )
    conn.commit()
    conn.close()

    return jsonify({"ok": True})

@app.route("/api/hymn-usage-records/<record_id>", methods=["DELETE"])
def delete_hymn_usage_record(record_id: str) -> Any:
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db()

    existing = conn.execute(
        "SELECT id FROM hymn_usage_records WHERE id = ? AND user_id = ?",
        (record_id, user_id),
    ).fetchone()

    if existing is None:
        conn.close()
        return jsonify({"error": "Hymn usage record not found."}), 404

    conn.execute(
        "DELETE FROM hymn_usage_records WHERE id = ? AND user_id = ?",
        (record_id, user_id),
    )
    conn.commit()
    conn.close()

    return jsonify({"ok": True})

@app.route("/api/members/<member_id>", methods=["DELETE"])
def delete_member(member_id: str) -> Any:
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db()

    existing = conn.execute(
        "SELECT id FROM members WHERE id = ? AND user_id = ?",
        (member_id, user_id),
    ).fetchone()

    if existing is None:
        conn.close()
        return jsonify({"error": "Member not found."}), 404

    conn.execute(
        "DELETE FROM pastoral_prayer_records WHERE member_id = ? AND user_id = ?",
        (member_id, user_id),
    )
    conn.execute(
        "DELETE FROM members WHERE id = ? AND user_id = ?",
        (member_id, user_id),
    )

    conn.commit()
    conn.close()

    return jsonify({"ok": True})

init_db()

if __name__ == "__main__":
    app.run(debug=True, port=5000)