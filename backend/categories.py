from flask import Blueprint, jsonify, request
from backend.db import get_db_connection, close_db_connection
import mysql.connector

categories_bp = Blueprint("categories_bp", __name__)

# GET all categories
@categories_bp.route('/categories', methods=['GET'])
def get_categories():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM Category")
        categories = cursor.fetchall()
        return jsonify(categories), 200

    except mysql.connector.Error:
        return jsonify({"error": "Failed to fetch categories"}), 500

    finally:
        close_db_connection(cursor, conn)


# ADD category
@categories_bp.route('/categories', methods=['POST'])
def add_category():
    data = request.json

    
    if not data or "categoryName" not in data:
        return jsonify({"error": "categoryName is required"}), 400

    if not data["categoryName"].strip():
        return jsonify({"error": "categoryName cannot be empty"}), 400

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = "INSERT INTO Category (categoryName) VALUES (%s)"
        cursor.execute(query, (data["categoryName"],))
        conn.commit()

        return jsonify({"message": "Category added successfully"}), 201

    except mysql.connector.IntegrityError:
        return jsonify({"error": "Category already exists"}), 409

    except mysql.connector.Error:
        return jsonify({"error": "Failed to add category"}), 500

    finally:
        close_db_connection(cursor, conn)
