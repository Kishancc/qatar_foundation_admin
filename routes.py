from flask import request, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from models import db, Admin, Opportunity
from app import app
import re
import secrets

# Helper function to validate email
def is_valid_email(email):
    pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    return re.match(pattern, email) is not None

# ===== AUTHENTICATION ROUTES =====

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request data"}), 400

    full_name = data.get('full_name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    confirm_password = data.get('confirm_password', '')

    # Validation
    if not full_name or not email or not password or not confirm_password:
        return jsonify({"error": "All fields are required"}), 400

    if not is_valid_email(email):
        return jsonify({"error": "Invalid email format"}), 400

    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    if password != confirm_password:
        return jsonify({"error": "Passwords do not match"}), 400

    # Check if email already exists
    if Admin.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 400

    # Create new admin
    admin = Admin(full_name=full_name, email=email)
    admin.set_password(password)

    try:
        db.session.add(admin)
        db.session.commit()
        return jsonify({"message": "Account created successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to create account"}), 500

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request data"}), 400

    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    remember = data.get('remember', False)

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    admin = Admin.query.filter_by(email=email).first()
    if not admin or not admin.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401

    login_user(admin, remember=remember)
    return jsonify({"message": "Login successful"}), 200

@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logout successful"}), 200

@app.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request data"}), 400

    email = data.get('email', '').strip().lower()

    if not email or not is_valid_email(email):
        return jsonify({"error": "Valid email is required"}), 400

    # Check if email exists (but don't reveal it)
    admin = Admin.query.filter_by(email=email).first()
    if admin:
        # Generate reset token (in real app, send email)
        reset_token = secrets.token_urlsafe(32)
        # In a real application, you would:
        # 1. Store the token with expiration in database
        # 2. Send email with reset link
        # For now, just print it
        reset_link = f"http://localhost:5000/reset-password?token={reset_token}"
        print(f"Password reset link for {email}: {reset_link}")

    # Always return success to prevent email enumeration
    return jsonify({"message": "If the email exists, a reset link has been sent"}), 200

# ===== OPPORTUNITY CRUD ROUTES =====

@app.route('/api/opportunities', methods=['GET'])
@login_required
def get_opportunities():
    opportunities = Opportunity.query.filter_by(admin_id=current_user.id).all()
    result = []
    for opp in opportunities:
        result.append({
            "id": opp.id,
            "name": opp.name,
            "duration": opp.duration,
            "start_date": opp.start_date,
            "description": opp.description,
            "skills": opp.skills.split(',') if opp.skills else [],
            "category": opp.category,
            "future_opportunities": opp.future_opportunities,
            "max_applicants": opp.max_applicants
        })
    return jsonify({"status": "success", "data": result}), 200

@app.route('/api/opportunities', methods=['POST'])
@login_required
def create_opportunity():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request data"}), 400

    name = data.get('name', '').strip()
    duration = data.get('duration', '').strip()
    start_date = data.get('start_date', '').strip()
    description = data.get('description', '').strip()
    skills = data.get('skills', '')
    category = data.get('category', '').strip()
    future_opportunities = data.get('future_opportunities', '').strip()
    max_applicants = data.get('max_applicants')

    # Validation
    if not all([name, duration, start_date, description, skills, category, future_opportunities]):
        return jsonify({"error": "All required fields must be provided"}), 400

    allowed_categories = ['technology', 'business', 'design', 'marketing', 'data', 'other']
    if category not in allowed_categories:
        return jsonify({"error": "Invalid category"}), 400

    # Convert skills to comma-separated string
    if isinstance(skills, list):
        skills = ','.join(skill.strip() for skill in skills)

    # Create opportunity
    opportunity = Opportunity(
        name=name,
        duration=duration,
        start_date=start_date,
        description=description,
        skills=skills,
        category=category,
        future_opportunities=future_opportunities,
        max_applicants=max_applicants,
        admin_id=current_user.id
    )

    try:
        db.session.add(opportunity)
        db.session.commit()
        return jsonify({
            "status": "success",
            "message": "Opportunity created successfully",
            "data": {
                "id": opportunity.id,
                "name": opportunity.name,
                "duration": opportunity.duration,
                "start_date": opportunity.start_date,
                "description": opportunity.description,
                "skills": opportunity.skills.split(',') if opportunity.skills else [],
                "category": opportunity.category,
                "future_opportunities": opportunity.future_opportunities,
                "max_applicants": opportunity.max_applicants
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to create opportunity"}), 500

@app.route('/api/opportunities/<int:opportunity_id>', methods=['GET'])
@login_required
def get_opportunity(opportunity_id):
    opportunity = Opportunity.query.filter_by(id=opportunity_id, admin_id=current_user.id).first()
    if not opportunity:
        return jsonify({"error": "Opportunity not found"}), 404

    return jsonify({
        "status": "success",
        "data": {
            "id": opportunity.id,
            "name": opportunity.name,
            "duration": opportunity.duration,
            "start_date": opportunity.start_date,
            "description": opportunity.description,
            "skills": opportunity.skills.split(',') if opportunity.skills else [],
            "category": opportunity.category,
            "future_opportunities": opportunity.future_opportunities,
            "max_applicants": opportunity.max_applicants
        }
    }), 200

@app.route('/api/opportunities/<int:opportunity_id>', methods=['PUT'])
@login_required
def update_opportunity(opportunity_id):
    opportunity = Opportunity.query.filter_by(id=opportunity_id, admin_id=current_user.id).first()
    if not opportunity:
        return jsonify({"error": "Opportunity not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request data"}), 400

    # Update fields
    if 'name' in data:
        opportunity.name = data['name'].strip()
    if 'duration' in data:
        opportunity.duration = data['duration'].strip()
    if 'start_date' in data:
        opportunity.start_date = data['start_date'].strip()
    if 'description' in data:
        opportunity.description = data['description'].strip()
    if 'skills' in data:
        skills = data['skills']
        if isinstance(skills, list):
            skills = ','.join(skill.strip() for skill in skills)
        opportunity.skills = skills
    if 'category' in data:
        category = data['category'].strip()
        allowed_categories = ['technology', 'business', 'design', 'marketing', 'data', 'other']
        if category not in allowed_categories:
            return jsonify({"error": "Invalid category"}), 400
        opportunity.category = category
    if 'future_opportunities' in data:
        opportunity.future_opportunities = data['future_opportunities'].strip()
    if 'max_applicants' in data:
        opportunity.max_applicants = data['max_applicants']

    try:
        db.session.commit()
        return jsonify({
            "status": "success",
            "message": "Opportunity updated successfully",
            "data": {
                "id": opportunity.id,
                "name": opportunity.name,
                "duration": opportunity.duration,
                "start_date": opportunity.start_date,
                "description": opportunity.description,
                "skills": opportunity.skills.split(',') if opportunity.skills else [],
                "category": opportunity.category,
                "future_opportunities": opportunity.future_opportunities,
                "max_applicants": opportunity.max_applicants
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update opportunity"}), 500

@app.route('/api/opportunities/<int:opportunity_id>', methods=['DELETE'])
@login_required
def delete_opportunity(opportunity_id):
    opportunity = Opportunity.query.filter_by(id=opportunity_id, admin_id=current_user.id).first()
    if not opportunity:
        return jsonify({"error": "Opportunity not found"}), 404

    try:
        db.session.delete(opportunity)
        db.session.commit()
        return jsonify({"status": "success", "message": "Opportunity deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to delete opportunity"}), 500