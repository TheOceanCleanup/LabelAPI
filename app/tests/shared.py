from models.user import User, Role
import bcrypt


def get_headers(db):
    api_key = "123"
    api_secret = "foobar"
    hashed = bcrypt.hashpw(api_secret.encode(), bcrypt.gensalt())
    user = User(
        email="test@example.com",
        API_KEY=api_key,
        API_SECRET=hashed
    )
    db.session.add(user)

    role = Role(
        role='image-admin',
        user=user
    )
    db.session.add(role)

    db.session.commit()

    headers = {
        'Authentication-Key': api_key,
        'Authentication-Secret': api_secret
    }

    return headers