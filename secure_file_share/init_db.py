from app import app, db
from app.models import User

with app.app_context():
    db.create_all()
    
    # Create test Ops user
    if not User.query.filter_by(email="ops@example.com").first():
        ops_user = User(email="ops@example.com", role="ops")
        ops_user.set_password("password")
        db.session.add(ops_user)
        db.session.commit()
        print("Test Ops user created!")