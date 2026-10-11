"""Infirmary Emergency Desk - Flask backend (Vercel version).

Why this differs from the local version:
  * Vercel functions have no permanent disk, so data lives in a Postgres database (Neon),
    including the voice messages (stored as bytes in the `audio` table).
  * Every request may run in a fresh copy of the program, so the priority queue (max-heap from
    pq.py) is rebuilt from the database's 'waiting' rows whenever it is needed.
Without DATABASE_URL (running on your own laptop) it falls back to a local SQLite file.
"""
import os, re, sqlite3, time
from flask import Flask, jsonify, request, session, Response, g
from werkzeug.exceptions import HTTPException
from werkzeug.security import generate_password_hash, check_password_hash
from pq import PriorityQueue
from page import HTML

BASE = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL") or ""
ON_VERCEL = bool(os.environ.get("VERCEL"))
COLLEGE_MAIL = re.compile(r"^[^\s@]+@[^\s@]+\.(ac\.in|edu|edu\.in)$", re.I)   # change to your college domain
SEV = {4: "Critical", 3: "High", 2: "Medium", 1: "Low"}
INFIRMARY_PHONE = os.environ.get("INFIRMARY_PHONE", "+91 90000 00000")
STAFF_CODE = os.environ.get("STAFF_CODE", "")          # set this in Vercel -> Settings -> Environment Variables
MAX_AUDIO = 3 * 1024 * 1024                            # Vercel allows ~4.5 MB per request

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me")
app.config.update(SESSION_COOKIE_SAMESITE="Lax", SESSION_COOKIE_SECURE=ON_VERCEL, MAX_CONTENT_LENGTH=4 * 1024 * 1024)

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(regno TEXT PRIMARY KEY, name TEXT, email TEXT UNIQUE, dob TEXT, pw_dob TEXT, pw_custom TEXT);
CREATE TABLE IF NOT EXISTS staff(id TEXT PRIMARY KEY, name TEXT, pw TEXT, email TEXT, designation TEXT);
CREATE TABLE IF NOT EXISTS requests(id SERIAL PRIMARY KEY, regno TEXT, name TEXT, age INTEGER, location TEXT, sev INTEGER,
    description TEXT, has_audio INTEGER DEFAULT 0, created DOUBLE PRECISION, status TEXT DEFAULT 'waiting', handled_by TEXT,
    for_other INTEGER DEFAULT 0, patient_regno TEXT, reporter TEXT);
CREATE TABLE IF NOT EXISTS audio(request_id INTEGER PRIMARY KEY, mime TEXT, data BYTEA);
"""


# ---------- database layer: Postgres on Vercel, SQLite file on a laptop ----------
class LocalCur:
    def __init__(self, c): self.cur = c.cursor()
    def execute(self, sql, args=()):
        self.cur.execute(sql.replace("%s", "?"), args); return self
    def fetchone(self): return self.cur.fetchone()
    def fetchall(self): return self.cur.fetchall()
    def close(self): self.cur.close()


class LocalDB:
    IntegrityError = sqlite3.IntegrityError
    def __init__(self, path):
        self.c = sqlite3.connect(path); self.c.row_factory = sqlite3.Row
    def cursor(self): return LocalCur(self.c)
    def script(self, sql):
        self.c.executescript(sql.replace("SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")
                                .replace("DOUBLE PRECISION", "REAL").replace("BYTEA", "BLOB"))
    def commit(self): self.c.commit()
    def rollback(self): self.c.rollback()
    def close(self): self.c.close()


def connect():
    if DATABASE_URL:
        import psycopg2, psycopg2.extras
        return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor, connect_timeout=10)
    if ON_VERCEL:
        raise RuntimeError("Database not connected. In Vercel add Storage > Neon (Postgres) to this project, then redeploy.")
    return LocalDB(os.path.join(BASE, "infirmary.db"))


_ready = False


def db():
    global _ready
    if "db" not in g:
        g.db = connect()
        if not _ready:                                    # create tables once per cold start
            try:
                if hasattr(g.db, "script"):
                    g.db.script(SCHEMA)
                else:
                    cur = g.db.cursor(); cur.execute(SCHEMA); cur.close()
                g.db.commit()
            except Exception:
                g.db.rollback()                           # another instance created them at the same time
            _ready = True
    return g.db


@app.teardown_appcontext
def close_db(_):
    d = g.pop("db", None)
    if d:
        d.close()


def qall(sql, args=()):
    cur = db().cursor(); cur.execute(sql, args); rows = cur.fetchall(); cur.close(); return rows


def qone(sql, args=()):
    cur = db().cursor(); cur.execute(sql, args); r = cur.fetchone(); cur.close(); return r


def run(sql, args=()):
    cur = db().cursor(); cur.execute(sql, args); return cur


def blob(b):
    if DATABASE_URL:
        import psycopg2
        return psycopg2.Binary(b)
    return b


@app.errorhandler(Exception)
def on_error(e):
    if isinstance(e, HTTPException):
        return jsonify(error=e.description), e.code
    app.logger.exception("server error")
    msg = str(e) if isinstance(e, RuntimeError) else "Server error. Please try again, or call the infirmary."
    return jsonify(error=msg), 500


# ---------- the priority queue (max-heap from pq.py) ----------
def build_heap():
    q = PriorityQueue()
    for r in qall("SELECT id, sev FROM requests WHERE status='waiting'"):
        q.push({"id": r["id"], "seq": r["id"], "sev": r["sev"]})
    return q


COLS = "id, regno, name, age, location, sev, description, has_audio, created, status, handled_by, for_other, patient_regno, reporter"


def row(r):
    return {"id": r["id"], "regno": r["regno"], "name": r["name"], "age": r["age"], "location": r["location"],
            "sev": r["sev"], "level": SEV[r["sev"]], "description": r["description"],
            "hasAudio": bool(r["has_audio"]), "created": r["created"], "status": r["status"], "by": r["handled_by"],
            "forOther": bool(r["for_other"]), "reporter": r["reporter"], "patientRegno": r["patient_regno"]}


def need(role):
    if session.get("role") != role:
        return jsonify(error="Please log in."), 401


# ---------- pages and settings ----------
@app.get("/")
def index():
    return Response(HTML, mimetype="text/html", headers={"Cache-Control": "no-cache"})


@app.get("/api/config")
def config():
    return jsonify(phone=INFIRMARY_PHONE, staffCode=bool(STAFF_CODE))


# ---------- registration and login ----------
@app.post("/api/staff/register")
def staff_register():
    d = request.get_json(force=True)
    name, email, desig = (d.get(k, "").strip() for k in ("name", "email", "designation"))
    pw = d.get("password", "")
    if not (name and email and desig and pw):
        return jsonify(error="Fill name, email, designation and password."), 400
    if not COLLEGE_MAIL.match(email):
        return jsonify(error="Use your college email (e.g. name@college.ac.in)."), 400
    if len(pw) < 6:
        return jsonify(error="Password must be at least 6 characters."), 400
    if STAFF_CODE and d.get("code", "").strip() != STAFF_CODE:
        return jsonify(error="Wrong staff registration code. Ask the infirmary in-charge."), 403
    try:
        run("INSERT INTO staff(id,name,pw,email,designation) VALUES(%s,%s,%s,%s,%s)",
            (email.lower(), name, generate_password_hash(pw), email.lower(), desig)).close()
        db().commit()
    except db().IntegrityError:
        db().rollback()
        return jsonify(error="This email is already registered. Please log in."), 409
    return jsonify(ok=True)


@app.post("/api/register")
def register():
    d = request.get_json(force=True)
    name, email, regno, dob = (d.get(k, "").strip() for k in ("name", "email", "regno", "dob"))
    regno = regno.upper()
    if not (name and regno and dob):
        return jsonify(error="Fill name, register number and DOB."), 400
    if not COLLEGE_MAIL.match(email):
        return jsonify(error="Use your college email (e.g. name@college.ac.in)."), 400
    pw = d.get("password", "")
    try:
        run("INSERT INTO users(regno,name,email,dob,pw_dob,pw_custom) VALUES(%s,%s,%s,%s,%s,%s)",
            (regno, name, email.lower(), dob, generate_password_hash(dob),
             generate_password_hash(pw) if pw else None)).close()
        db().commit()
    except db().IntegrityError:
        db().rollback()
        return jsonify(error="Already registered. Please log in."), 409
    return jsonify(ok=True)


@app.post("/api/login")
def login():
    d = request.get_json(force=True)
    role, uid, pw = d.get("role"), d.get("username", "").strip(), d.get("password", "")
    if role == "staff":
        s = qone("SELECT * FROM staff WHERE id=%s", (uid.lower(),))
        if s and check_password_hash(s["pw"], pw):
            desig = s["designation"] or "Staff"
            session.clear(); session.update(role="staff", id=s["id"], name=s["name"], designation=desig,
                                            label=f"{s['name']} ({desig})")
            return jsonify(role="staff", name=s["name"])
    else:
        u = qone("SELECT * FROM users WHERE regno=%s", (uid.upper(),))
        if u and (check_password_hash(u["pw_dob"], pw) or (u["pw_custom"] and check_password_hash(u["pw_custom"], pw))):
            session.clear(); session.update(role="student", id=u["regno"], name=u["name"], dob=u["dob"])
            return jsonify(role="student", name=u["name"], regno=u["regno"], dob=u["dob"])
    return jsonify(error="Wrong username or password."), 401


@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify(ok=True)


@app.get("/api/me")
def me():
    return jsonify({k: session.get(k) for k in ("role", "id", "name", "dob", "designation")})


# ---------- emergency requests ----------
@app.post("/api/requests")
def create_request():
    if (e := need("student")): return e
    f = request.form
    name, loc, desc = f.get("name", "").strip(), f.get("location", "").strip(), f.get("description", "").strip()
    try:
        age, sev = int(f.get("age", "")), int(f.get("sev", ""))
    except ValueError:
        return jsonify(error="Age and severity are required."), 400
    for_other = 1 if f.get("for_other") == "1" else 0
    patient_regno = f.get("patient_regno", "").strip().upper() if for_other else session["id"]
    audio = request.files.get("audio")
    data = audio.read() if audio else b""
    if not (name and loc) or sev not in SEV:
        return jsonify(error="Please fill name, age and your location."), 400
    if not (desc or data):
        return jsonify(error="Add a description or a voice message."), 400
    if len(data) > MAX_AUDIO:
        return jsonify(error="Voice message is too large. Please record a shorter one."), 400
    cur = run("INSERT INTO requests(regno,name,age,location,sev,description,has_audio,created,for_other,patient_regno,reporter) "
              "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
              (session["id"], name, age, loc, sev, desc, 1 if data else 0, time.time(), for_other, patient_regno,
               session["name"]))
    rid = cur.fetchone()["id"]; cur.close()
    if data:
        run("INSERT INTO audio(request_id,mime,data) VALUES(%s,%s,%s)",
            (rid, audio.mimetype or "audio/webm", blob(data))).close()
    db().commit()                       # no heap push needed: the heap is rebuilt from the database
    return jsonify(id=rid)


@app.get("/api/my-requests")
def my_requests():
    if (e := need("student")): return e
    order = [x["id"] for x in build_heap().sorted_list()]
    rows = qall(f"SELECT {COLS} FROM requests WHERE regno=%s ORDER BY id DESC", (session["id"],))
    out = []
    for r in rows:
        d = row(r)
        d["position"] = order.index(r["id"]) + 1 if r["id"] in order else None
        d["total"] = len(order)
        out.append(d)
    return jsonify(out)


@app.get("/api/queue")
def get_queue():
    if (e := need("staff")): return e
    q = build_heap()
    ordered, heap = q.sorted_list(), [f"{x['sev']}@{x['seq']}" for x in q.a]
    ids = [x["id"] for x in ordered]
    rows = {}
    if ids:
        rows = {r["id"]: row(r) for r in qall(
            f"SELECT {COLS} FROM requests WHERE id IN ({','.join(['%s'] * len(ids))})", ids)}
    mine = qall(f"SELECT {COLS} FROM requests WHERE status='accepted' AND handled_by=%s ORDER BY id", (session["label"],))
    return jsonify(queue=[rows[i] for i in ids if i in rows], heap=heap, inProgress=[row(r) for r in mine])


@app.post("/api/queue/accept")
def accept():
    if (e := need("staff")): return e
    for _ in range(5):                  # retry if another staff member took the same case a moment earlier
        top = build_heap().extract_max()          # most urgent request leaves the heap
        if not top:
            return jsonify(error="No emergencies waiting."), 404
        cur = run("UPDATE requests SET status='accepted', handled_by=%s WHERE id=%s AND status='waiting' RETURNING id",
                  (session["label"], top["id"]))
        got = cur.fetchone(); cur.close(); db().commit()
        if got:
            return jsonify(id=top["id"])
    return jsonify(error="Busy, please try again."), 409


@app.post("/api/requests/<int:rid>/resolve")
def resolve(rid):
    if (e := need("staff")): return e
    run("UPDATE requests SET status='done' WHERE id=%s AND handled_by=%s", (rid, session["label"])).close()
    db().commit()
    return jsonify(ok=True)


@app.get("/api/audio/<int:rid>")
def audio(rid):
    r = qone("SELECT regno, has_audio FROM requests WHERE id=%s", (rid,))
    if not r or not r["has_audio"] or session.get("role") not in ("staff", "student") or \
            (session["role"] == "student" and session["id"] != r["regno"]):
        return jsonify(error="Not found."), 404
    a = qone("SELECT mime, data FROM audio WHERE request_id=%s", (rid,))
    if not a:
        return jsonify(error="Not found."), 404
    return Response(bytes(a["data"]), mimetype=a["mime"] or "audio/webm", headers={"Cache-Control": "private, max-age=3600"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
