from flask import Blueprint, jsonify, request, g
from backend.db import get_db_connection, close_db_connection
from backend.auth import token_required
import mysql.connector

budget_bp = Blueprint("budget_bp", __name__)

@budget_bp.route('/budget', methods=['GET'])
@token_required
def get_budgets():
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT
            b.budgetId,
            c.categoryName,
            b.percentage,
            b.budgetMonth,
            b.budgetYear
        FROM Budget b
        JOIN Category c
            ON b.categoryId = c.categoryId
        WHERE b.userId = %s
        """

        cursor.execute(query, (g.current_user["user_id"],))
        budgets = cursor.fetchall()

        return jsonify(budgets), 200

    except mysql.connector.Error:
        return jsonify({
            "error": "Failed to fetch budgets"
        }), 500

    finally:
        close_db_connection(cursor, conn)

@budget_bp.route('/budget', methods=['POST'])
@token_required
def add_budget():

    data = request.json

    if not data:
        return jsonify({
            "error": "Request body is required"
        }), 400

    required_fields = [
        "categoryId",
        "percentage",
        "budgetMonth",
        "budgetYear"
    ]

    for field in required_fields:
        if field not in data:
            return jsonify({
                "error": f"{field} is required"
            }), 400

    if data["percentage"] <= 0:
        return jsonify({
            "error": "Percentage must be greater than 0"
        }), 400

    if data["percentage"] > 100:
        return jsonify({
            "error": "Percentage cannot exceed 100"
        }), 400

    if data["budgetMonth"] < 1 or data["budgetMonth"] > 12:
        return jsonify({
            "error": "Month must be between 1 and 12"
        }), 400

    if data["budgetYear"] < 2000:
        return jsonify({
            "error": "Invalid year"
        }), 400

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check current allocation
        query = """
        SELECT COALESCE(SUM(percentage), 0) AS total
        FROM Budget
        WHERE userId = %s
        AND budgetMonth = %s
        AND budgetYear = %s
        """

        cursor.execute(
            query,
            (
                g.current_user["user_id"],
                data["budgetMonth"],
                data["budgetYear"]
            )
        )

        result = cursor.fetchone()
        current_total = float(result["total"])

        if current_total + data["percentage"] > 100:
            return jsonify({
                "error": "Total budget allocation cannot exceed 100%"
            }), 400

        query = """
        INSERT INTO Budget
        (    userId,
            categoryId,
            percentage,
            budgetMonth,
            budgetYear
        )
        VALUES (%s, %s, %s, %s, %s)
        """

        cursor.execute(
            query,
            (
                g.current_user["user_id"],
                data["categoryId"],
                data["percentage"],
                data["budgetMonth"],
                data["budgetYear"]
            )
        )

        conn.commit()

        return jsonify({
            "message": "Budget added successfully"
        }), 201

    except mysql.connector.IntegrityError:
        return jsonify({
            "error": "Invalid categoryId"
        }), 400

    except mysql.connector.Error:
        return jsonify({
            "error": "Failed to add budget"
        }), 500

    finally:
        close_db_connection(cursor, conn)

@budget_bp.route('/budget/<int:id>', methods=['PUT'])
@token_required
def update_budget(id):

    data = request.json

    if not data:
        return jsonify({
            "error": "Request body is required"
        }), 400

    required_fields = [
        "categoryId",
        "percentage",
        "budgetMonth",
        "budgetYear"
    ]

    for field in required_fields:
        if field not in data:
            return jsonify({
                "error": f"{field} is required"
            }), 400

    if data["percentage"] <= 0:
        return jsonify({
            "error": "Percentage must be greater than 0"
        }), 400

    if data["percentage"] > 100:
        return jsonify({
            "error": "Percentage cannot exceed 100"
        }), 400

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT COALESCE(SUM(percentage), 0) AS total
        FROM Budget
        WHERE userId = %s
        AND budgetMonth = %s
        AND budgetYear = %s
        AND budgetId != %s
        """

        cursor.execute(
            query,
            (
                g.current_user["user_id"],
                data["budgetMonth"],
                data["budgetYear"],
                id
            )
        )

        result = cursor.fetchone()
        current_total = float(result["total"])

        if current_total + data["percentage"] > 100:
            return jsonify({
                "error": "Total budget allocation cannot exceed 100%"
            }), 400

        query = """
        UPDATE Budget
        SET
            categoryId = %s,
            percentage = %s,
            budgetMonth = %s,
            budgetYear = %s
        WHERE budgetId = %s
        AND userId = %s
        """

        cursor.execute(
            query,
            (
                data["categoryId"],
                data["percentage"],
                data["budgetMonth"],
                data["budgetYear"],
                id,
                g.current_user["user_id"]
            )
        )

        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({
                "error": "Budget not found"
            }), 404

        return jsonify({
            "message": "Budget updated successfully"
        }), 200

    except mysql.connector.Error:
        return jsonify({
            "error": "Failed to update budget"
        }), 500

    finally:
        close_db_connection(cursor, conn)


@budget_bp.route('/budget/<int:id>', methods=['DELETE'])
@token_required
def delete_budget(id):

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        DELETE FROM Budget
        WHERE budgetId = %s
        AND userId = %s
        """

        cursor.execute(
            query,
            (id,
                g.current_user["user_id"]
            )
        )

        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({
                "error": "Budget not found"
            }), 404

        return jsonify({
            "message": "Budget deleted successfully"
        }), 200

    except mysql.connector.Error:
        return jsonify({
            "error": "Failed to delete budget"
        }), 500

    finally:
        close_db_connection(cursor, conn)
    
