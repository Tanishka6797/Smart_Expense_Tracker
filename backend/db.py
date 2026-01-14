import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="Expense_Tracker"
    )

def close_db_connection(cursor, conn):
    if cursor:
        cursor.close()
    if conn:
        conn.close()