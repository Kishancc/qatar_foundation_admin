from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, Admin, Opportunity
from config import Config
import os
import secrets
import re

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

# Serve static files from sky directory
@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory('sky', filename)

# Serve the main admin.html as root
@app.route('/')
def index():
    return send_from_directory('sky', 'admin.html')

# Import routes
from routes import *

# Create database tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)