import bcrypt
from initialize_database import get_db

def hash_password(password):
    """
    Hashes a password securely using bcrypt.
    """
    salt = bcrypt.gensalt()  # Generates a new salt
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')  # Store as a string in DB


def authenticate_user(username_or_email, password):
    """
    Authenticates a user by checking the username or email and verifying the password.
    """
    try:
        conn = get_db()
        cursor = conn.cursor()

        # ✅ Support login with either username or email
        cursor.execute("SELECT password FROM users WHERE username = %s OR email = %s", 
                       (username_or_email, username_or_email))
        user = cursor.fetchone()
        conn.close()

        if not user:
            print("❌ User not found")
            return False

        stored_hashed_password = user[0]

        # ✅ Ensure the stored password is in bytes before checking
        if isinstance(stored_hashed_password, str):
            stored_hashed_password = stored_hashed_password.encode("utf-8")

        # ✅ Check if password matches
        if bcrypt.checkpw(password.encode("utf-8"), stored_hashed_password):
            return True
        else:
            print("❌ Password mismatch")
            return False

    except Exception as e:
        print(f"🚨 Error during authentication: {e}")
        return False
