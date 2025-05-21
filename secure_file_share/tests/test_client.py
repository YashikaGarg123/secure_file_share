import unittest
from app import app, db

class ClientTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.ctx = app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_client_signup(self):
        response = self.app.post('/client/signup', json={"email": "client@example.com", "password": "password"})
        self.assertIn("encrypted_url", response.json)