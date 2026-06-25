from flask import Blueprint, jsonify, g
from backend.db import get_db_connection, close_db_connection
from backend.auth import token_required
import mysql.connector
from datetime import datetime

dashboard_bp = Blueprint("dashboard_bp", __name__)

@dashboard_bp.route('/dashboard/summary', methods=['GET'])
@token_required
def dashboard_summary():

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        current_month = datetime.now().month
        current_year = datetime.now().year

        # Get Monthly Income
        income_query = """
        SELECT COALESCE(SUM(amount), 0) AS totalIncome
        FROM Income
        WHERE userId = %s
        AND incomeMonth = %s
        AND incomeYear = %s
        """

        cursor.execute(
            income_query,
            (
                g.current_user["user_id"],
                current_month,
                current_year
            )
        )

        income_result = cursor.fetchone()
        total_income = float(income_result["totalIncome"])

        # Get Monthly Expenses
        expense_query = """
        SELECT COALESCE(SUM(amount), 0) AS totalExpenses
        FROM Expense
        WHERE userId = %s
        AND MONTH(expenseDate) = %s
        AND YEAR(expenseDate) = %s
        """

        cursor.execute(
            expense_query,
            (
                g.current_user["user_id"],
                current_month,
                current_year
            )
        )

        expense_result = cursor.fetchone()
        total_expenses = float(expense_result["totalExpenses"])

        # Calculate Savings
        savings = total_income - total_expenses

        # Calculate Savings Percentage
        savings_percentage = 0

        if total_income > 0:
            savings_percentage = round(
                (savings / total_income) * 100,
                2
            )

        return jsonify({
            "income": total_income,
            "expenses": total_expenses,
            "savings": savings,
            "savingsPercentage": savings_percentage
        }), 200

    except mysql.connector.Error:
        return jsonify({
            "error": "Failed to fetch dashboard summary"
        }), 500

    finally:
        close_db_connection(cursor, conn)

@dashboard_bp.route('/dashboard/category-summary', methods=['GET'])
@token_required
def category_summary():

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        current_month = datetime.now().month
        current_year = datetime.now().year

        # Get total monthly income
        income_query = """
        SELECT COALESCE(SUM(amount),0) AS totalIncome
        FROM Income
        WHERE userId = %s
        AND incomeMonth = %s
        AND incomeYear = %s
        """

        cursor.execute(
            income_query,
            (
                g.current_user["user_id"],
                current_month,
                current_year
            )
        )

        total_income = float(cursor.fetchone()["totalIncome"])

        # Get category wise budget and spending
        query = """
        SELECT
            c.categoryName,
            b.percentage,

            COALESCE(
                SUM(e.amount),
                0
            ) AS spent

        FROM Budget b

        JOIN Category c
            ON b.categoryId = c.categoryId

        LEFT JOIN Expense e
            ON e.categoryId = c.categoryId
            AND e.userId = b.userId
            AND MONTH(e.expenseDate) = b.budgetMonth
            AND YEAR(e.expenseDate) = b.budgetYear

        WHERE b.userId = %s
        AND b.budgetMonth = %s
        AND b.budgetYear = %s

        GROUP BY
            c.categoryName,
            b.percentage
        """

        cursor.execute(
            query,
            (
                g.current_user["user_id"],
                current_month,
                current_year
            )
        )

        rows = cursor.fetchall()

        result = []

        for row in rows:

            allocated = (
                total_income *
                row["percentage"]
            ) / 100

            remaining = allocated - float(row["spent"])

            result.append({
                "category": row["categoryName"],
                "percentage": row["percentage"],
                "allocated": round(allocated, 2),
                "spent": float(row["spent"]),
                "remaining": round(remaining, 2)
            })

        return jsonify(result), 200

    except mysql.connector.Error:
        return jsonify({
            "error": "Failed to fetch category summary"
        }), 500

    finally:
        close_db_connection(cursor, conn)
    
@dashboard_bp.route('/dashboard/lifetime-savings', methods=['GET'])
@token_required
def lifetime_savings():

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Total Income
        income_query = """
        SELECT COALESCE(SUM(amount),0) AS totalIncome
        FROM Income
        WHERE userId = %s
        """

        cursor.execute(
            income_query,
            (
                g.current_user["user_id"],
            )
        )

        total_income = float(
            cursor.fetchone()["totalIncome"]
        )

        # Total Expenses
        expense_query = """
        SELECT COALESCE(SUM(amount),0) AS totalExpenses
        FROM Expense
        WHERE userId = %s
        """

        cursor.execute(
            expense_query,
            (
                g.current_user["user_id"],
            )
        )

        total_expenses = float(
            cursor.fetchone()["totalExpenses"]
        )

        total_savings = (
            total_income -
            total_expenses
        )

        return jsonify({
            "totalIncome": total_income,
            "totalExpenses": total_expenses,
            "totalSavings": total_savings
        }), 200

    except mysql.connector.Error:
        return jsonify({
            "error": "Failed to fetch lifetime savings"
        }), 500

    finally:
        close_db_connection(cursor, conn)

@dashboard_bp.route('/reports/monthly', methods=['GET'])
@token_required
def monthly_report():

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        current_month = datetime.now().month
        current_year = datetime.now().year

        # Total Income
        income_query = """
        SELECT COALESCE(SUM(amount),0) AS totalIncome
        FROM Income
        WHERE userId=%s
        AND incomeMonth=%s
        AND incomeYear=%s
        """

        cursor.execute(
            income_query,
            (
                g.current_user["user_id"],
                current_month,
                current_year
            )
        )

        total_income = float(cursor.fetchone()["totalIncome"])

        # Total Expenses
        expense_query = """
        SELECT COALESCE(SUM(amount),0) AS totalExpenses
        FROM Expense
        WHERE userId=%s
        AND MONTH(expenseDate)=%s
        AND YEAR(expenseDate)=%s
        """

        cursor.execute(
            expense_query,
            (
                g.current_user["user_id"],
                current_month,
                current_year
            )
        )

        total_expenses = float(cursor.fetchone()["totalExpenses"])

        # Savings
        savings = total_income - total_expenses

        if total_income > 0:
            savings_percentage = round(
                (savings / total_income) * 100,
                2
            )
        else:
            savings_percentage = 0

        # Highest Expense Category
        highest_query = """
        SELECT
            c.categoryName,
            SUM(e.amount) AS totalSpent
        FROM Expense e
        JOIN Category c
            ON e.categoryId = c.categoryId
        WHERE e.userId=%s
        AND MONTH(e.expenseDate)=%s
        AND YEAR(e.expenseDate)=%s
        GROUP BY c.categoryName
        ORDER BY totalSpent DESC
        LIMIT 1
        """

        cursor.execute(
            highest_query,
            (
                g.current_user["user_id"],
                current_month,
                current_year
            )
        )

        highest = cursor.fetchone()

        if highest:
            highest_category = highest["categoryName"]
            highest_amount = float(highest["totalSpent"])
        else:
            highest_category = None
            highest_amount = 0

        # Budget Analysis
        budget_query = """
        SELECT
            c.categoryName,
            b.percentage,
            COALESCE(SUM(e.amount),0) AS spent

        FROM Budget b

        JOIN Category c
            ON b.categoryId = c.categoryId

        LEFT JOIN Expense e
            ON e.categoryId = b.categoryId
            AND e.userId = b.userId
            AND MONTH(e.expenseDate)=b.budgetMonth
            AND YEAR(e.expenseDate)=b.budgetYear

        WHERE b.userId=%s
        AND b.budgetMonth=%s
        AND b.budgetYear=%s

        GROUP BY
            c.categoryName,
            b.percentage
        """

        cursor.execute(
            budget_query,
            (
                g.current_user["user_id"],
                current_month,
                current_year
            )
        )

        rows = cursor.fetchall()

        budget_status = []

        for row in rows:

            allocated = (
                total_income *
                row["percentage"]
            ) / 100

            spent = float(row["spent"])

            remaining = allocated - spent

            budget_status.append({
                "category": row["categoryName"],
                "percentage": row["percentage"],
                "allocated": round(allocated,2),
                "spent": spent,
                "remaining": round(remaining,2)
            })

        return jsonify({

            "month": current_month,
            "year": current_year,

            "income": total_income,

            "expenses": total_expenses,

            "savings": savings,

            "savingsPercentage": savings_percentage,

            "highestExpenseCategory": highest_category,

            "highestExpenseAmount": highest_amount,

            "budgetStatus": budget_status

        }),200

    except mysql.connector.Error:
        return jsonify({
            "error":"Failed to generate monthly report"
        }),500

    finally:
        close_db_connection(cursor,conn)