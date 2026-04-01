from flask import Blueprint, request, jsonify
from database import SessionLocal
from models import User
from passlib.hash import sha256_crypt as bcrypt
import jwt, datetime

auth = Blueprint("auth", __name__)

SECRET = "supersecret"

@auth.route("/register", methods=["POST"])
def register():
    db = SessionLocal()
    data = request.json

    hashed_password = bcrypt.hash(data["password"])

    user = User(
        email=data["email"],
        password=hashed_password
    )

    db.add(user)
    db.commit()

    return {"message": "User created successfully"}

@auth.route("/login", methods=["POST"])
def login():
    db = SessionLocal()
    data = request.json

    user = db.query(User).filter(User.email == data["email"]).first()

    if not user:
        return {"error": "User not found"}

    if not bcrypt.verify(data["password"], user.password):
        return {"error": "Wrong password"}

    token = jwt.encode({
        "user_id": user.id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }, SECRET, algorithm="HS256")

    return {"token": token}