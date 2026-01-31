from flask import Flask
from flask_cors import CORS

from backend.auth import auth_bp
from backend.categories import categories_bp
from backend.expenses import expenses_bp

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://127.0.0.1:5500"}})

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(categories_bp)
app.register_blueprint(expenses_bp)

if __name__ == "__main__":
    app.run(debug=True, port=8086)
