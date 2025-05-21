import unittest
from app import app, db

class AuthTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.ctx = app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_ops_login_success(self):
        from app.models import User
        user = User(email="ops@example.com", role="ops")
        user.set_password("password")
        db.session.add(user)
        db.session.commit()

        response = self.app.post('/ops/login', json={"email": "ops@example.com", "password": "password"})
        self.assertEqual(response.status_code, 200)