from flask import Blueprint, request, jsonify, send_file
from app.models import User, File
from app import app, db, bcrypt
import jwt
import datetime
from functools import wraps
import os
from werkzeug.utils import secure_filename

auth_bp = Blueprint('auth', __name__)

def authenticate_ops(auth_header):
    if not auth_header:
        return None
    try:
        token = auth_header.split(" ")[1]
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        user = User.query.get(data['user_id'])
        if user.role != 'ops':
            return None
        return user
    except:
        return None

def authenticate_client(auth_header):
    if not auth_header:
        return None
    try:
        token = auth_header.split(" ")[1]
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        user = User.query.get(data['user_id'])
        if user.role != 'client' or not user.verified:
            return None
        return user
    except:
        return None

@auth_bp.route('/ops/login', methods=['POST'])
def ops_login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if user and user.check_password(data['password']) and user.role == 'ops':
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }, app.config['SECRET_KEY'])
        return jsonify({'token': token}), 200
    return jsonify({"error": "Invalid credentials"}), 401