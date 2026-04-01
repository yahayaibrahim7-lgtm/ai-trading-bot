from flask import Flask, jsonify, request, render_template, g
from flask_cors import CORS

from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base

from passlib.hash import bcrypt
import jwt
import datetime
import requests
import os
import hmac
import hashlib
from contextlib import contextmanager
from functools import wraps
import os
from dotenv import load_dotenv

load_dotenv()

SECRET = os.environ.get("JWT_SECRET")
PAYSTACK_SECRET = os.environ.get("PAYSTACK_SECRET")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN")

DATABASE_URL = "sqlite:///./test.db"

# 🔥 MT5 AI ENGINE
from mt5_service import get_signal

# ==============================
# CONFIG  (all secrets from env)
# ==============================
import os

SECRET = os.environ.get("JWT_SECRET")
PAYSTACK_SECRET = os.environ.get("PAYSTACK_SECRET")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN")        # simple static token for admin routes


# ==============================
# DATABASE
# ==============================
engine       = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base         = declarative_base()


class User(Base):
    __tablename__ = "users"

    id       = Column(Integer, primary_key=True)
    email    = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    vip      = Column(Boolean, default=False)
    chat_id  = Column(String, nullable=True)


Base.metadata.create_all(bind=engine)


@contextmanager
def get_db():
    """Yield a DB session and always close it, even on error."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==============================
# APP INIT
# ==============================
app = Flask(__name__)
CORS(app)  # tighten in production: CORS(app, origins=["https://yourdomain.com"])


# ==============================
# HELPERS / DECORATORS
# ==============================
def decode_token(token: str) -> dict | None:
    """Return payload dict or None. Raises nothing — callers check None."""
    try:
        return jwt.decode(token, SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None   # token expired — client should re-login
    except jwt.InvalidTokenError:
        return None   # tampered or malformed


def require_auth(f):
    """Decorator: injects current_user into the route or returns 401/403."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
        if not token:
            return jsonify({"error": "Missing token"}), 401

        payload = decode_token(token)
        if payload is None:
            return jsonify({"error": "Invalid or expired token"}), 401

        with get_db() as db:
            user = db.query(User).filter(User.id == payload["user_id"]).first()
            if not user:
                return jsonify({"error": "User not found"}), 401
            # Detach from session so the route can use the object freely
            db.expunge(user)
            g.current_user = user

        return f(*args, **kwargs)
    return wrapper


def require_vip(f):
    """Must be stacked BELOW @require_auth."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not g.current_user.vip:
            return jsonify({"error": "VIP subscription required"}), 403
        return f(*args, **kwargs)
    return wrapper


def require_admin(f):
    """Simple static-token admin guard. Replace with role-based auth for production."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get("X-Admin-Token", "")
        if not hmac.compare_digest(token, ADMIN_TOKEN):
            return jsonify({"error": "Forbidden"}), 403
        return f(*args, **kwargs)
    return wrapper


def verify_paystack_signature(payload: bytes, signature: str) -> bool:
    """Verify Paystack webhook HMAC-SHA512 signature."""
    expected = hmac.new(
        PAYSTACK_SECRET.encode(), payload, hashlib.sha512
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


# ==============================
# HOME
# ==============================
@app.route("/")
def home():
    return jsonify({"status": "AI Trading Backend running"})


# ==============================
# AUTH
# ==============================
@app.route("/auth/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}

    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    with get_db() as db:
        if db.query(User).filter(User.email == email).first():
            return jsonify({"error": "Email already registered"}), 409

        user = User(email=email, password=bcrypt.hash(password))
        db.add(user)
        db.commit()

    return jsonify({"message": "User created"}), 201


@app.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}

    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    with get_db() as db:
        user = db.query(User).filter(User.email == email).first()

    # Deliberate vague error — don't reveal whether the email exists
    if not user or not bcrypt.verify(password, user.password):
        return jsonify({"error": "Invalid credentials"}), 401

    now = datetime.datetime.now(datetime.timezone.utc)
    token = jwt.encode(
        {
            "user_id": user.id,
            "email":   user.email,
            "exp":     now + datetime.timedelta(days=7),
            "iat":     now,
        },
        SECRET,
        algorithm="HS256",
    )

    return jsonify({"token": token})


# ==============================
# PAYSTACK
# ==============================
@app.route("/pay", methods=["POST"])
@require_auth
def pay():
    email = g.current_user.email   # use the authenticated user's email, not user input

    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET}",
        "Content-Type":  "application/json",
    }
    data = {"email": email, "amount": 500000}   # ₦5,000 in kobo

    try:
        res = requests.post(
            "https://api.paystack.co/transaction/initialize",
            json=data,
            headers=headers,
            timeout=10,
        )
        res.raise_for_status()
    except requests.RequestException as e:
        return jsonify({"error": "Payment gateway error", "detail": str(e)}), 502

    return jsonify(res.json())


@app.route("/verify/<reference>")
@require_auth
def verify(reference):
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET}"}

    try:
        res = requests.get(
            f"https://api.paystack.co/transaction/verify/{reference}",
            headers=headers,
            timeout=10,
        )
        res.raise_for_status()
    except requests.RequestException as e:
        return jsonify({"error": "Payment gateway error", "detail": str(e)}), 502

    payload = res.json()

    if payload.get("data", {}).get("status") != "success":
        return jsonify({"error": "Payment not successful"}), 402

    # Only upgrade the currently authenticated user — ignore email in Paystack response
    with get_db() as db:
        user = db.query(User).filter(User.id == g.current_user.id).first()
        if user:
            user.vip = True
            db.commit()

    return jsonify({"message": "VIP activated"})


# ==============================
# TELEGRAM CHAT ID
# ==============================
@app.route("/save-chat-id", methods=["POST"])
@require_auth
def save_chat_id():
    data    = request.get_json(silent=True) or {}
    chat_id = data.get("chat_id", "").strip()

    if not chat_id:
        return jsonify({"error": "chat_id is required"}), 400

    with get_db() as db:
        user = db.query(User).filter(User.id == g.current_user.id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        user.chat_id = chat_id
        db.commit()

    return jsonify({"message": "Chat ID saved"})


# ==============================
# SIGNAL  (VIP only)
# ==============================
SUPPORTED_PAIRS = ["USDJPY", "EURUSD", "XAUUSD"]

@app.route("/signal")
def signal():
    results = [get_signal(pair) for pair in SUPPORTED_PAIRS]
    return jsonify(results)


# ==============================
# ADMIN DASHBOARD  (protected)
# ==============================
@app.route("/admin/users")
@require_admin
def get_users():
    with get_db() as db:
        users = db.query(User).all()
        return jsonify([
            {"email": u.email, "vip": u.vip, "chat_id": u.chat_id}
            for u in users
        ])


@app.route("/admin")
@require_admin
def admin():
    return render_template("admin.html")

@app.route("/webhook/paystack", methods=["POST"])
def paystack_webhook():
    data = request.json

    if data["event"] == "charge.success":
        email = data["data"]["customer"]["email"]

        db = SessionLocal()
        user = db.query(User).filter(User.email == email).first()

        if user:
            user.vip = True
            db.commit()

    return {"status": "ok"}

# ==============================
# GLOBAL ERROR HANDLERS
# ==============================
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method not allowed"}), 405


@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal server error"}), 500


# ==============================
# RUN
# ==============================
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
    # debug=True must never be True in production
    app.run(debug=os.environ.get("FLASK_DEBUG", "false").lower() == "true")
# imports
from flask import Flask

app = Flask(_name_)

# routes
@app.route("/")
def home():
    return "API running"

# MORE ROUTES...
# /login
# /signal
# /admin
import os

if __name_ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
