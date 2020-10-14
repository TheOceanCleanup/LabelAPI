from models.user import User
from common.db import db
import bcrypt


def get_headers():
    api_key = "123"
    api_secret = "foobar"
    hashed = bcrypt.hashpw(api_secret.encode(), bcrypt.gensalt())
    user = User(
        email="test@example.com",
        API_KEY=api_key,
        API_SECRET=hashed
    )
    db.session.add(user)
    db.session.commit()
    
    headers = {
        'Authentication-Key': api_key,
        'Authentication-Secret': api_secret
    }
    
    return headers