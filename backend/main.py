from flask import Flask
from flask_cors import CORS

from backend.auth import auth_bp
from backend.categories import categories_bp
from backend.expenses import expenses_bp
from backend.income import income_bp
from backend.budget import budget_bp
from backend.dashboard import dashboard_bp

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://127.0.0.1:5500"}})

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(categories_bp)
app.register_blueprint(expenses_bp)
app.register_blueprint(income_bp)
app.register_blueprint(budget_bp)
app.register_blueprint(dashboard_bp)

if __name__ == "__main__":
    app.run(debug=True, port=8086)
