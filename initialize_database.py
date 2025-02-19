import os
import psycopg2
import psycopg2.extras
import bcrypt
from dotenv import load_dotenv

load_dotenv()

# ✅ Load PostgreSQL Configuration
DB_HOST = os.getenv("POSTGRES_HOST")
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASS = os.getenv("POSTGRES_PASSWORD")


# ✅ Check if all environment variables are set
if not all([DB_HOST, DB_NAME, DB_USER, DB_PASS]):
    raise ValueError("🚨 Missing PostgreSQL environment variables! Check your .env file.")

# ✅ PostgreSQL Database Connection
def get_db():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        return conn
    except Exception as e:
        print(f"🚨 Database connection error: {e}")
        raise

# ✅ Initialize PostgreSQL Database
def init_db():
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                # ✅ Create users table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL,
                        is_verified BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                    );
                """)

                # ✅ Create extraction_history table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS extraction_history (
                        id SERIAL PRIMARY KEY,
                        username TEXT NOT NULL REFERENCES users(username) ON DELETE CASCADE,
                        document_name TEXT NOT NULL,
                        total_rows INTEGER NOT NULL,
                        total_time REAL NOT NULL,
                        timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                    );
                """)

                # ✅ Create removed_users table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS removed_users (
                        id SERIAL PRIMARY KEY,
                        username TEXT UNIQUE NOT NULL REFERENCES users(username) ON DELETE CASCADE,
                        removed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                    );
                """)

                # ✅ Create email_verifications table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS email_verifications (
                        email TEXT PRIMARY KEY REFERENCES users(email) ON DELETE CASCADE,
                        token TEXT UNIQUE NOT NULL,
                        expires_at TIMESTAMPTZ NOT NULL
                    );
                """)

                conn.commit()

                # ✅ Ensure admin user exists
                cursor.execute("SELECT EXISTS(SELECT 1 FROM users WHERE username = 'admin')")
                admin_exists = cursor.fetchone()[0]

                if not admin_exists:
                    hashed_password = bcrypt.hashpw("admin123".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
                    cursor.execute("INSERT INTO users (username, email, password, is_verified) VALUES (%s, %s, %s, TRUE)", 
                                   ("admin", "admin@example.com", hashed_password))
                    conn.commit()

                print("✅ PostgreSQL Database initialized successfully!")

    except Exception as e:
        print(f"🚨 Error initializing database: {e}")
