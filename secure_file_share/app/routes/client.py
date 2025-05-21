from flask import Blueprint, request, jsonify
from app.models import User
from app import db, bcrypt, app
import jwt
import datetime
import secrets

client_bp = Blueprint('client', __name__)

@client_bp.route('/client/signup', methods=['POST'])
def client_signup():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 400

    new_user = User(
        email=email,
        role='client',
        verification_token=secrets.token_urlsafe(64)
    )
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    verify_url = f"https://yourdomain.com/verify-email/ {new_user.verification_token}"
    encrypted_url = encrypt_url(verify_url)  # Implement this function
    return jsonify({"encrypted_url": encrypted_url}), 201

@client_bp.route('/client/verify-email/<token>', methods=['GET'])
def verify_email(token):
    user = User.query.filter_by(verification_token=token).first()
    if not user:
        return jsonify({"error": "Invalid token"}), 400

    user.verified = True
    db.session.commit()
    return jsonify({"message": "Email verified successfully"}), 200

@client_bp.route('/client/login', methods=['POST'])
def client_login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if user and user.check_password(data['password']) and user.verified:
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }, app.config['SECRET_KEY'])
        return jsonify({'token': token}), 200
    return jsonify({"error": "Invalid credentials or not verified"}), 401