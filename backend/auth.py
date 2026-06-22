from flask import Blueprint, jsonify, request
from backend.db import get_db_connection, close_db_connection
import mysql.connector
import hashlib
import jwt
import os
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import g

auth_bp = Blueprint("auth_bp", __name__)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token(user_id, email):
    payload = {
        "user_id" : user_id,
        "email" : email,
        "exp" : datetime.now(timezone.utc) + timedelta(hours=24)
    }

    token = jwt.encode(
        payload,
        os.getenv("JWT_SECRET_KEY"),
        algorithm= "HS256" #HMAC + SHA256
    )
    return token

def verify_token(token):
    try:
        payload = jwt.decode(
            token,
            os.getenv("JWT_SECRET_KEY"),
            algorithms=['HS256']
        )
        return payload
    
    except jwt.ExpiredSignatureError:
        return None
    
    except jwt.InvalidTokenError:
        return None

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return jsonify({
                "error": "Authorization header is missing"
            }), 401
        
        try:
            token = auth_header.split(" ")[1]

        except IndexError:
            return jsonify({
                "error":"Invalid Token Format"
            }), 401
        
        payload = verify_token(token)

        if payload is None:
            return jsonify({
                "error":"Invalid or Expired token"
            }), 401
        
        g.current_user = payload
        
        return f(*args,**kwargs)
    return decorated


# user registration
@auth_bp.route('/auth/register', methods=['POST'])
def register():
    data = request.json

    if not data:
        return jsonify ({"error": "Request body is required"}), 400
    
    required_fields = ["name", "emailId", "password"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"{field} is required"}), 400
        
    if not data["name"].strip():
        return jsonify({"error":"Name cannot be empty"}), 400
    
    if not data["emailId"].strip():
        return jsonify({"error": "Email cannot be empty"}), 400
    
    if len(data["password"]) < 6:
        return jsonify({"error": "Password must be atleast 6 charachters"}), 400
    
    hashed_password = hash_password(data["password"])

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        INSERT INTO Expense_Users (name, emailId, password)
        VALUES (%s, %s, %s)
        """
        cursor.execute(query, (data["name"], data["emailId"], hashed_password ))

        conn.commit()

        return jsonify({"message": "User registered successfully"}), 201
    
    # checks for duplicate emails
    except mysql.connector.IntegrityError:
        return jsonify({"error":"Email already Exists"}), 409
    
    # DB error
    except mysql.connector.Error:
        return jsonify({"error": "Registartion failed"}), 500
    
    finally:
        close_db_connection(cursor, conn)


# user login 
@auth_bp.route('/auth/login', methods=['POST'])
def login():
    data = request.json

    if not data:
        return jsonify({"error": "Request body is required"}), 400

    # Validate required fields
    if "emailId" not in data or "password" not in data:
        return jsonify({"error": "emailId and password are required"}), 400

    hashed_password = hash_password(data["password"])

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT id, name, emailId
        FROM Expense_Users
        WHERE emailId = %s AND password = %s
        """
        cursor.execute(query, (data["emailId"], hashed_password))
        user = cursor.fetchone()

        # Invalid credentials
        if not user:
            return jsonify({"error": "Invalid email or password"}), 401

        token = generate_token(
            user["id"],
            user["emailId"]
        )
        return jsonify({
            "message": "Login successful",
            "token": token,
            "user": user
        }), 200
    
    except mysql.connector.Error:
        return jsonify({"error": "Login failed"}), 500

    finally:
        close_db_connection(cursor, conn)