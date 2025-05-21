import unittest
import os
from app import app, db
from app.models import User, File

class FileTestCase(unittest.TestCase):
    def setUp(self):
        # Set up test Flask app context and database
        self.app = app.test_client()
        self.ctx = app.app_context()
        self.ctx.push()
        db.create_all()

        # Create Ops user for upload
        self.ops_user = User(email="ops@example.com", role="ops")
        self.ops_user.set_password("password")
        db.session.add(self.ops_user)
        db.session.commit()

        # Login as Ops to get token
        login_data = {
            "email": "ops@example.com",
            "password": "password"
        }
        response = self.app.post('/ops/login', json=login_data)
        self.ops_token = response.json['token']

        # Create Client user
        self.client_user = User(email="client@example.com", role="client", verified=True)
        self.client_user.set_password("password")
        db.session.add(self.client_user)
        db.session.commit()

        # Login as Client to get token
        login_data_client = {
            "email": "client@example.com",
            "password": "password"
        }
        response = self.app.post('/client/login', json=login_data_client)
        self.client_token = response.json['token']

        # Setup upload folder
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])

    def tearDown(self):
        # Clean up after each test
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _auth_header(self, token):
        return {"Authorization": f"Bearer {token}"}

    def test_upload_valid_file_type(self):
        """Test uploading a valid .pptx file"""
        with open('test.pptx', 'w') as f:
            f.write("dummy content")

        with open('test.pptx', 'rb') as f:
            data = {
                'file': f
            }
            response = self.app.post(
                '/upload',
                headers=self._auth_header(self.ops_token),
                data=data,
                content_type='multipart/form-data'
            )

        self.assertEqual(response.status_code, 201)
        self.assertIn("download_link", response.json)

        os.remove('test.pptx')

    def test_upload_invalid_file_type(self):
        """Test uploading an invalid file type (.txt) should fail"""
        with open('test.txt', 'w') as f:
            f.write("dummy content")

        with open('test.txt', 'rb') as f:
            data = {
                'file': f
            }
            response = self.app.post(
                '/upload',
                headers=self._auth_header(self.ops_token),
                data=data,
                content_type='multipart/form-data'
            )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid file type", response.json["error"])

        os.remove('test.txt')

    def test_list_files_as_client(self):
        """Test client can list all files"""
        new_file = File(filename="demo.pptx", file_type=".pptx", download_token="abc123")
        db.session.add(new_file)
        db.session.commit()

        response = self.app.get(
            '/files',
            headers=self._auth_header(self.client_token)
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.json) > 0)

    def test_download_file_success(self):
        """Test client can download a file via download token"""
        new_file = File(filename="report.docx", file_type=".docx", download_token="xyz789")
        db.session.add(new_file)
        db.session.commit()

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], "report.docx")
        with open(file_path, 'w') as f:
            f.write("Sample document content.")

        response = self.app.get(
            '/download-file/xyz789',
            headers=self._auth_header(self.client_token)
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("attachment", response.headers['Content-Disposition'])

        os.remove(file_path)

    def test_download_file_unauthorized(self):
        """Test non-client user cannot download file"""
        new_file = File(filename="secret.xlsx", file_type=".xlsx", download_token="denied123")
        db.session.add(new_file)
        db.session.commit()

        response = self.app.get('/download-file/denied123')
        self.assertEqual(response.status_code, 401)

    def test_upload_missing_file(self):
        """Test upload fails when no file is provided"""
        response = self.app.post(
            '/upload',
            headers=self._auth_header(self.ops_token)
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("No file provided", response.json["error"])