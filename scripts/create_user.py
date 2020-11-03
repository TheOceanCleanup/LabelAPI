from models.user import User, Role
from main import app
from common.db import db

email = ""

with app.app_context():
    user = User.find_or_create(email)
    api_key, api_secret = user.generate_api_key()
    print(f"User credentials:\n\tAPI Key: {api_key}\n\tAPI secret: {api_secret}")
    role = Role(role="image-admin", user=user)
    db.session.commit()
