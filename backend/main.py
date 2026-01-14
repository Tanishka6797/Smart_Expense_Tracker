from flask import Flask, jsonify, request
from backend.db import get_db_connection, close_db_connection



app = Flask(__name__)

# USER APIs

@app.route('/users', methods=['GET'])
def get_users():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("Select* From Expense_Users")
        users = cursor.fetchall()

        return jsonify(users)
    finally:
        close_db_connection(cursor,conn)

@app.route('/users/<int:id>', methods=['GET'])
def get_user_by_id(id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = "Select* From Expense_Users WHERE id=%s"
        cursor.execute(query,(id,))
        user = cursor.fetchone()

        if user is None:
            return jsonify({"message:User not found"}), 404
        
        return jsonify(user)
    
    finally:
        close_db_connection(cursor,conn)

# CATEGORY APIs
@app.route('/categories', methods =['GET'])
def get_categories():
    conn=None
    cursor=None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("Select* From Category")
        categories = cursor.fetchall()

        return jsonify(categories)

    finally:
        close_db_connection(cursor,conn)

@app.route('/categories', methods=['POST'])
def add_category():
    data = request.json
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = "INSERT INTO Category (categoryName) VALUES (%s)"
        cursor.execute(query, (data['categoryName'],))
        conn.commit()

        return jsonify({"message": "Category added"}), 201
    finally:
        close_db_connection(cursor, conn)

#EXPENSE 

@app.route('/expenses', methods=['GET'])
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
        JOIN Expense_Users u ON e.userId = u.id
        JOIN Category c ON e.categoryId = c.categoryId
        """

        cursor.execute(query)
        expenses = cursor.fetchall()

        return jsonify(expenses)
    finally:
        close_db_connection(cursor, conn)

@app.route('/expenses', methods=['POST'])
def add_expense():
    data = request.json
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        INSERT INTO Expense (userId, categoryId, amount, expenseDate, description)
        VALUES (%s, %s, %s, %s, %s)
        """

        cursor.execute(query, (
            data['userId'],
            data['categoryId'],
            data['amount'],
            data['expenseDate'],
            data.get('description')
        ))

        conn.commit()
        return jsonify({"message": "Expense added"}), 201
    finally:
        close_db_connection(cursor, conn)

@app.route('/expenses/<int:id>', methods=['PUT'])
def update_expense(id):
    data = request.json
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        UPDATE Expense
        SET userId = %s,
            categoryId = %s,
            amount = %s,
            expenseDate = %s,
            description = %s
        WHERE expenseId = %s
        """

        cursor.execute(query, (
            data['userId'],
            data['categoryId'],
            data['amount'],
            data['expenseDate'],
            data.get('description'),
            id
        ))
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"message": "Expense not found"}), 404

        return jsonify({"message": "Expense updated successfully"})
    finally:
        close_db_connection(cursor, conn)


@app.route('/expenses/<int:id>', methods=['DELETE'])
def delete_expense(id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = "DELETE FROM Expense WHERE expenseId = %s"
        cursor.execute(query, (id,))
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"message": "Expense not found"}), 404

        return jsonify({"message": "Expense deleted successfully"})
    finally:
        close_db_connection(cursor, conn)


if __name__ == '__main__':
    app.run(debug=True, port=8086)