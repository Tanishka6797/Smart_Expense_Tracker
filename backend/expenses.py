from flask import Blueprint, jsonify, request, g
from backend.db import get_db_connection, close_db_connection
import mysql.connector
from backend.auth import token_required

expenses_bp = Blueprint("expenses_bp", __name__)

@expenses_bp.route('/expenses', methods=['GET'])
@token_required
def get_expenses():
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT
            e.amount,
            e.expenseDate,
            e.description,
            u.name AS userName,
            c.categoryName
        FROM Expense e
        JOIN Expense_Users u
            ON e.userId = u.id
        JOIN Category c
            ON e.categoryId = c.categoryId
        WHERE e.userId = %s
        """

        cursor.execute(query, (g.current_user["user_id"],))
        expenses = cursor.fetchall()

        return jsonify(expenses), 200

    except mysql.connector.Error:
        return jsonify({"error": "Failed to fetch expenses"}), 500

    finally:
        close_db_connection(cursor, conn)

@expenses_bp.route('/expenses', methods=['POST'])
@token_required
def add_expense():
    data = request.json

    if not data:
        return jsonify({"error": "Request body is required"}), 400

    required_fields = ["categoryId", "amount", "expenseDate"]

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
        INSERT INTO Expense
        (userId, categoryId, amount, expenseDate, description)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(
            query,
            (
                g.current_user["user_id"],
                data["categoryId"],
                data["amount"],
                data["expenseDate"],
                data.get("description")
            )
        )
        conn.commit()

        return jsonify({
            "message": "Expense added successfully"
        }), 201

    except mysql.connector.IntegrityError:
        return jsonify({
            "error": "Invalid categoryId"
        }), 400

    except mysql.connector.Error:
        return jsonify({
            "error": "Failed to add expense"
        }), 500

    finally:
        close_db_connection(cursor, conn)

@expenses_bp.route('/expenses/<int:id>', methods=['PUT'])
@token_required
def update_expense(id):
    data = request.json

    if not data:
        return jsonify({"error": "Request body is required"}), 400

    required_fields = ["categoryId", "amount", "expenseDate"]

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
        UPDATE Expense
        SET
            categoryId = %s,
            amount = %s,
            expenseDate = %s,
            description = %s
        WHERE expenseId = %s
        AND userId = %s
        """

        cursor.execute(
            query,
            (
                data["categoryId"],
                data["amount"],
                data["expenseDate"],
                data.get("description"),
                id,
                g.current_user["user_id"]
            )
        )

        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Expense not found"}), 404

        return jsonify({
            "message": "Expense updated successfully"
        }), 200

    except mysql.connector.Error:
        return jsonify({
            "error": "Failed to update expense"
        }), 500

    finally:
        close_db_connection(cursor, conn)

@expenses_bp.route('/expenses/<int:id>', methods=['DELETE'])
@token_required
def delete_expense(id):
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        DELETE FROM Expense
        WHERE expenseId = %s
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
            return jsonify({"error": "Expense not found"}), 404

        return jsonify({
            "message": "Expense deleted successfully"
        }), 200

    except mysql.connector.Error:
        return jsonify({
            "error": "Failed to delete expense"
        }), 500

    finally:
        close_db_connection(cursor, conn)
