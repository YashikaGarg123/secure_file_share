from flask import Blueprint, request, jsonify, send_file, current_app
from app.models import User, File
from app.routes.auth import authenticate_ops
from app import db
import os

files_bp = Blueprint('files', __name__)

@files_bp.route('/upload', methods=['POST'])
def upload_file():
    ops_user = authenticate_ops(request.headers.get('Authorization'))
    if not ops_user:
        return jsonify({"error": "Unauthorized"}), 401

    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ['.pptx', '.docx', '.xlsx']:
        return jsonify({"error": "Invalid file type"}), 400

    filename = secure_filename(file.filename)
    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))

    new_file = File(filename=filename, file_type=ext)
    db.session.add(new_file)
    db.session.commit()

    return jsonify({
        "message": "File uploaded successfully",
        "download_link": f"/download-file/{new_file.download_token}"
    }), 201

@files_bp.route('/files', methods=['GET'])
def list_files():
    from app.routes.auth import authenticate_client
    client = authenticate_client(request.headers.get('Authorization'))
    if not client:
        return jsonify({"error": "Unauthorized"}), 401

    files = File.query.all()
    result = [{"filename": f.filename, "url": f"/download-file/{f.download_token}"} for f in files]
    return jsonify(result), 200

@files_bp.route('/download-file/<token>', methods=['GET'])
def download_file(token):
    from app.routes.auth import authenticate_client
    client = authenticate_client(request.headers.get('Authorization'))
    if not client:
        return jsonify({"error": "Unauthorized"}), 401

    file_record = File.query.filter_by(download_token=token).first()
    if not file_record:
        return jsonify({"error": "File not found"}), 404

    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file_record.filename)
    return send_file(file_path, as_attachment=True)