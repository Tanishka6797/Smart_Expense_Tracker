from flask import Blueprint, jsonify, request, g
from backend.db import get_db_connection, close_db_connection
from backend.auth import token_required
import mysql.connector

income_bp = Blueprint("income_bp", __name__)

#get all income records
@income_bp.route('/income', methods=['GET'])
@token_required
def get_income():
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT *
            FROM Income
            WHERE userId = %s
        """
        cursor.execute(query, (g.current_user["user_id"],))
        incomes = cursor.fetchall()

        return jsonify(incomes), 200

    except mysql.connector.Error:
        return jsonify({"error": "Failed to fetch income records"}), 500

    finally:
        close_db_connection(cursor, conn)

@income_bp.route('/income', methods=['POST'])
@token_required
def add_income():

    data = request.json

    if not data:
        return jsonify({"error": "Request body is required"}), 400

    required_fields = ["amount", "incomeMonth", "incomeYear"]

    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"{field} is required"}), 400

    if data["amount"] <= 0:
        return jsonify({"error": "Amount must be greater than 0"}), 400

    if data["incomeMonth"] < 1 or data["incomeMonth"] > 12:
        return jsonify({"error": "Month must be between 1 and 12"}), 400

    if data["incomeYear"] < 2000:
        return jsonify({"error": "Invalid year"}), 400

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        INSERT INTO Income
        (userId, amount, incomeMonth, incomeYear)
        VALUES (%s, %s, %s, %s)
        """

        cursor.execute(
            query,
            (
                g.current_user["user_id"],
                data["amount"],
                data["incomeMonth"],
                data["incomeYear"]
            )
        )

        conn.commit()

        return jsonify({
            "message": "Income added successfully"
        }), 201

    except mysql.connector.Error:
        return jsonify({
            "error": "Failed to add income"
        }), 500

    finally:
        close_db_connection(cursor, conn)


@income_bp.route('/income/<int:id>', methods=['PUT'])
@token_required
def update_income(id):

    data = request.json

    if not data:
        return jsonify({"error": "Request body is required"}), 400

    required_fields = ["amount", "incomeMonth", "incomeYear"]

    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"{field} is required"}), 400

    if data["amount"] <= 0:
        return jsonify({"error": "Amount must be greater than 0"}), 400

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        UPDATE Income
        SET amount = %s,
            incomeMonth = %s,
            incomeYear = %s
        WHERE incomeId = %s
        AND userId = %s
        """

        cursor.execute(
            query,
            (
                data["amount"],
                data["incomeMonth"],
                data["incomeYear"],
                id,
                g.current_user["user_id"]
            )
        )

        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({
                "error": "Income record not found"
            }), 404

        return jsonify({
            "message": "Income updated successfully"
        }), 200

    except mysql.connector.Error:
        return jsonify({
            "error": "Failed to update income"
        }), 500

    finally:
        close_db_connection(cursor, conn)

@income_bp.route('/income/<int:id>', methods=['DELETE'])
@token_required
def delete_income(id):

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        DELETE FROM Income
        WHERE incomeId = %s
        AND userId = %s
        """

        cursor.execute(
            query,
            (
                id,
                g.current_user["user_id"]
            )
        )

        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({
                "error": "Income record not found"
            }), 404

        return jsonify({
            "message": "Income deleted successfully"
        }), 200

    except mysql.connector.Error:
        return jsonify({
            "error": "Failed to delete income"
        }), 500

    finally:
        close_db_connection(cursor, conn)
