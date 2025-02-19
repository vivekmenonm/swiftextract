from flask import Flask, request, jsonify, send_file, stream_with_context, Response, session
from flask_session import Session  # ✅ Import Flask-Session
import multiprocessing
import os
import secrets
import json
import tempfile
from initialize_database import init_db, get_db
from user_authentication import authenticate_user, hash_password
from pdf_processing import process_pdf
from email_verification import send_email_verification
from credentials_validation import is_valid_username, is_strong_password, is_valid_email
import time
from datetime import datetime, timedelta  # Import datetime and timedelta
import psycopg2
import psycopg2.extras
from psycopg2.extras import DictCursor
from pdf2image import convert_from_path
import bcrypt
import pandas as pd
from flask_cors import CORS
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)
# ✅ Configure Flask session to persist data
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"  # Uses file-based session storage
Session(app)  # ✅ Initialize session

load_dotenv()

app.config['SECRET_KEY'] = 'Genaiapplication'

init_db()


def save_extracted_data_to_excel(extracted_data, filename):
    df = pd.DataFrame(extracted_data)
    excel_path = os.path.join(tempfile.gettempdir(), filename)
    df.to_excel(excel_path, index=False)
    print(f"Excel file saved at: {excel_path}")
    return excel_path


@app.route("/register", methods=["POST"])
def register_user():
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    # Validate email format
    if not is_valid_email(email):
        return jsonify({"error": "Invalid email format"}), 400

    # Validate password strength
    if not is_strong_password(password):
        return jsonify({"error": "Weak password! Must be at least 8 characters, include 1 uppercase, 1 number, and 1 special character."}), 400

    try:
        conn = get_db()
        cursor = conn.cursor()

        # Check if user exists
        cursor.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, email))
        if cursor.fetchone():
            return jsonify({"error": "Username or email already registered"}), 400

        # Hash password
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        # Insert user with is_verified = FALSE
        cursor.execute("""
            INSERT INTO users (username, email, password, is_verified) 
            VALUES (%s, %s, %s, FALSE)
        """, (username, email, hashed_password))

        # Generate a verification token
        verification_token = secrets.token_urlsafe(32)
        expiry_time = datetime.utcnow() + timedelta(hours=24)  # Token expires in 24 hours

        # Store token in database
        cursor.execute("""
            INSERT INTO email_verifications (email, token, expires_at) 
            VALUES (%s, %s, %s)
        """, (email, verification_token, expiry_time))

        conn.commit()

        # Send Verification Email
        verification_link = f"https://yourfrontend.com/verify-email?token={verification_token}"
        email_sent = send_email_verification(email, verification_link)

        if not email_sent:
            return jsonify({"error": "Failed to send verification email. Try again later."}), 500

        return jsonify({"message": "User registered! Please check your email for verification."}), 201

    except Exception as e:
        print(f"🚨 Registration Error: {e}")
        return jsonify({"error": "Internal server error"}), 500

    

# ✅ Login with username OR email
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    login_identifier = data.get("login")  # Can be either username or email
    password = data.get("password")

    if not login_identifier or not password:
        return jsonify({"error": "Username/email and password are required"}), 400

    try:
        conn = get_db()
        cursor = conn.cursor()

        # ✅ Check if user exists (by username OR email)
        cursor.execute("""
            SELECT username, email, password, is_verified 
            FROM users 
            WHERE username = %s OR email = %s
        """, (login_identifier, login_identifier))

        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not user:
            return jsonify({"error": "Invalid credentials"}), 401

        username, email, hashed_password, is_verified = user

        # ✅ Ensure stored password is in bytes
        if isinstance(hashed_password, str):
            hashed_password = hashed_password.encode("utf-8")

        # ✅ Verify password using bcrypt
        if not bcrypt.checkpw(password.encode("utf-8"), hashed_password):
            return jsonify({"error": "Invalid credentials"}), 401

        # ✅ Ensure user has verified their email before logging in
        if not is_verified:
            return jsonify({"error": "Please verify your email before logging in"}), 403

        # ✅ Store session data
        session['username'] = username

        return jsonify({"message": "Login successful!", "username": username}), 200

    except Exception as e:
        print(f"🚨 Error during login: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/change_password', methods=['POST'])
def change_password():
    data = request.get_json()

    # ✅ Check for missing parameters
    if not data or "username" not in data or "current_password" not in data or "new_password" not in data or "confirm_password" not in data:
        return jsonify({"error": "Missing required parameters"}), 400

    username = data["username"]
    current_password = data["current_password"]
    new_password = data["new_password"]
    confirm_password = data["confirm_password"]

    # ✅ Check if new passwords match
    if new_password != confirm_password:
        return jsonify({"error": "New password and confirmation do not match"}), 400

    try:
        conn = get_db()
        cursor = conn.cursor()

        # ✅ Retrieve stored hashed password
        cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "User not found"}), 404

        stored_hashed_password = user[0]

        # ✅ Ensure stored password is bytes
        if isinstance(stored_hashed_password, str):
            stored_hashed_password = stored_hashed_password.encode('utf-8')

        # ✅ Verify current password
        if not bcrypt.checkpw(current_password.encode(), stored_hashed_password):
            return jsonify({"error": "Current password is incorrect"}), 401

        # ✅ Hash the new password
        hashed_new_password = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode('utf-8')

        # ✅ Update the password in the database
        cursor.execute("UPDATE users SET password = %s WHERE username = %s", (hashed_new_password, username))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"message": "Password changed successfully!"}), 200

    except Exception as e:
        print(f"🚨 Error changing password: {e}")
        return jsonify({"error": "Internal server error"}), 500


# ✅ Create User Endpoint
@app.route("/create_user", methods=["POST"])
def create_user():
    data = request.json
    admin_username = data.get("admin_username")
    admin_password = data.get("admin_password")
    new_username = data.get("new_username")
    new_password = data.get("new_password")

    if admin_username != "admin" or not authenticate_user(admin_username, admin_password):
        return jsonify({"error": "Only admin can create users"}), 403

    try:
        conn = get_db()
        cursor = conn.cursor()
        hashed_password = hash_password(new_password)
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (new_username, hashed_password))
        conn.commit()
        return jsonify({"message": "User created successfully"}), 201
    except psycopg2.IntegrityError:
        return jsonify({"error": "Username already exists"}), 400
    finally:
        conn.close()

# Logout endpoint to clear the session
@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)  # Remove 'username' from session
    return jsonify({"message": "Logged out successfully!"})


@app.route("/extract_text_stream", methods=["POST"])
def process_pdfs_stream():
    if "pdf" not in request.files or "prompt" not in request.form or "username" not in request.form or "password" not in request.form:
        return jsonify({"error": "Missing required parameters"}), 400

    username = request.form["username"]
    password = request.form["password"]

    if not authenticate_user(username, password):
        return jsonify({"error": "Invalid credentials"}), 401

    pdf_files = request.files.getlist("pdf")
    prompt = request.form["prompt"]

    temp_dir = tempfile.mkdtemp()
    pdf_paths = []
    total_pages_global = 0  # ✅ Track total pages globally

    for pdf_file in pdf_files:
        original_filename = pdf_file.filename
        safe_filename = "".join(c for c in original_filename if c.isalnum() or c in (" ", ".", "_")).strip()
        pdf_path = os.path.join(temp_dir, safe_filename)
        pdf_file.save(pdf_path)
        pdf_paths.append(pdf_path)

        # ✅ Count total pages per PDF before processing
        images = convert_from_path(pdf_path, fmt="jpeg")
        total_pages_global += len(images)

    print(f"Total pages across all PDFs: {total_pages_global}")

    queue = multiprocessing.Queue()
    processes = []
    processed_pages = 0  # ✅ Track pages processed globally

    for pdf_path in pdf_paths:
        process = multiprocessing.Process(target=process_pdf, args=(pdf_path, prompt, username, queue, total_pages_global))
        processes.append(process)
        process.start()

    def generate():
        nonlocal processed_pages
        all_extracted_data = []
        total_time = 0
        total_rows_extracted = 0
        skipped_pages = []
        active_processes = len(pdf_paths)
        document_progress = {}

        while active_processes > 0:
            data = queue.get()

            if "document_name" in data and "progress" in data:
                doc_name = data["document_name"]
                doc_progress = data["progress"]
                document_progress[doc_name] = doc_progress  

                # ✅ Yield per-document progress
                yield f"data: {json.dumps({'document_name': doc_name, 'progress': doc_progress})}\n\n"

            if "current_page_processed" in data:
                processed_pages += 1  
                total_progress = round((processed_pages / total_pages_global) * 100, 2)

                # ✅ Yield total progress dynamically
                yield f"data: {json.dumps({'total_progress': total_progress})}\n\n"

            if "extracted_data" in data and isinstance(data["extracted_data"], list):
                all_extracted_data.extend(data["extracted_data"])
            if "skipped_pages" in data and isinstance(data["skipped_pages"], list):
                skipped_pages.extend(data["skipped_pages"])

            if "total_time" in data:
                total_time += data["total_time"]
            if "total_rows_extracted" in data:
                total_rows_extracted += data["total_rows_extracted"]

            if "completed" in data:
                active_processes -= 1  

        for process in processes:
            process.join()

        # ✅ Save final extracted data
        if all_extracted_data:
            total_time = round(total_time, 2)
            avg_time_per_row = round(total_time / total_rows_extracted, 2) if total_rows_extracted > 0 else 0
            timestamp = int(time.time())
            combined_filename = f"output_data_{timestamp}.xlsx"
            combined_path = save_extracted_data_to_excel(all_extracted_data, combined_filename)

            # ✅ Final yield with completion status & download link
            yield f"data: {json.dumps({'completed': True, 'download_link': f'/download_excel?filename={combined_filename}', 'total_time': total_time, 'total_rows_extracted': total_rows_extracted, 'avg_time_per_row': avg_time_per_row})}\n\n"

    return Response(stream_with_context(generate()), content_type="text/event-stream")


@app.route("/download_excel", methods=["GET"])
def download_excel():
    filename = request.args.get("filename")
    file_path = os.path.join(tempfile.gettempdir(), filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return jsonify({"error": "File not found"}), 404


@app.route("/user_list", methods=["GET"])
def get_user_list():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT username FROM users")
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return jsonify({"users": users})


@app.route("/history", methods=["POST"])
def show_extraction_history():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    target_username = data.get("target_username", "").strip()  # ✅ Ensure target_username is properly formatted

    # ✅ Check authentication
    if not authenticate_user(username, password):
        return jsonify({"error": "Invalid credentials"}), 401

    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # ✅ If the user is NOT an admin, show ONLY their history
    if username != "admin":
        target_username = username  # ✅ Force non-admins to see only their own history

    # ✅ Admin can filter by a specific user OR see all users
    if username == "admin":
        if target_username and target_username != "All Users":
            print(f"Admin fetching history for user: {target_username}")  # ✅ Debugging Log
            cursor.execute("SELECT * FROM extraction_history WHERE username = %s ORDER BY timestamp DESC", (target_username,))
        else:
            print("Admin fetching history for all users")  # ✅ Debugging Log
            cursor.execute("SELECT * FROM extraction_history ORDER BY timestamp DESC")
    else:
        print(f"User fetching history for self: {username}")  # ✅ Debugging Log
        cursor.execute("SELECT * FROM extraction_history WHERE username = %s ORDER BY timestamp DESC", (username,))

    history = cursor.fetchall()
    conn.close()

    return jsonify({
        "history": [
            {
                "username": row["username"],  # ✅ Include username
                "document_name": row["document_name"],
                "total_rows": row["total_rows"],
                "total_time": row["total_time"],
                "avg_time_per_field": round(float(row["total_time"]) / row["total_rows"], 2) if row["total_rows"] > 0 else 0,
                "timestamp": row["timestamp"]
            }
            for row in history
        ]
    })


@app.route("/stats", methods=["GET"])
def get_statistics():
    conn = get_db()
    cursor = conn.cursor()

    # Get total unique users who have processed at least one document
    cursor.execute("SELECT COUNT(DISTINCT username) FROM extraction_history")
    total_unique_users = cursor.fetchone()[0]

    # Get total documents processed
    cursor.execute("SELECT COUNT(DISTINCT document_name) FROM extraction_history")
    total_documents = cursor.fetchone()[0]

    # Get total rows processed
    cursor.execute("SELECT COALESCE(SUM(total_rows), 0) FROM extraction_history")
    total_rows = cursor.fetchone()[0]

    conn.close()

    return jsonify({
        "total_users": total_unique_users,
        "total_documents_processed": total_documents,
        "total_rows_processed": total_rows
    })


@app.route("/user_stats", methods=["POST"])
def get_user_statistics():
    data = request.get_json()
    admin_username = data.get("admin_username")
    admin_password = data.get("admin_password")

    # Admin authentication
    if admin_username != "admin" or not authenticate_user(admin_username, admin_password):
        return jsonify({"error": "Only admin can access user statistics"}), 403

    conn = get_db()
    cursor = conn.cursor(cursor_factory=DictCursor)  # Use DictCursor for row access by column names

    cursor.execute("""
        SELECT 
            username, 
            COUNT(DISTINCT document_name) AS total_documents, 
            SUM(total_rows) AS total_rows, 
            SUM(total_time) AS total_time
        FROM extraction_history
        GROUP BY username
    """)
    
    user_stats = cursor.fetchall()
    conn.close()

    return jsonify({
        "user_statistics": [
            {
                "username": row["username"],
                "total_documents": row["total_documents"],
                "total_rows": row["total_rows"],
                "avg_time_per_row": round(row["total_time"] / row["total_rows"], 2) if row["total_rows"] > 0 else 0
            }
            for row in user_stats
        ]
    })


@app.route("/user_stats_self", methods=["POST"])
def get_user_statistics_self():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    # Authenticate user
    if not authenticate_user(username, password):
        return jsonify({"error": "Invalid credentials"}), 401

    conn = get_db()
    cursor = conn.cursor(cursor_factory=DictCursor)

    cursor.execute("""
        SELECT 
            COUNT(DISTINCT document_name) AS total_documents, 
            COALESCE(SUM(total_rows), 0) AS total_rows, 
            COALESCE(SUM(total_time), 0) AS total_time
        FROM extraction_history
        WHERE username = %s
    """, (username,))
    
    user_stat = cursor.fetchone()
    conn.close()

    # Handle case where no rows exist for user
    total_documents = user_stat["total_documents"] if user_stat else 0
    total_rows = user_stat["total_rows"] if user_stat else 0
    total_time = user_stat["total_time"] if user_stat else 0

    avg_time_per_row = round(total_time / total_rows, 2) if total_rows > 0 else 0

    return jsonify({
        "username": username,
        "total_documents": total_documents,
        "total_rows": total_rows,
        "avg_time_per_row": avg_time_per_row
    })


@app.route("/remove_user", methods=["POST"])
def remove_user():
    data = request.get_json()
    admin_username = data.get("admin_username")
    admin_password = data.get("admin_password")
    target_username = data.get("target_username")

    # Authenticate as admin
    if admin_username != "admin" or not authenticate_user(admin_username, admin_password):
        return jsonify({"error": "Only admin can remove users"}), 403

    # Prevent deletion of the admin account
    if target_username == "admin":
        return jsonify({"error": "Admin account cannot be deleted"}), 403

    try:
        conn = get_db()
        cursor = conn.cursor()

        # Check if the user exists before attempting deletion
        cursor.execute("SELECT * FROM users WHERE username = %s", (target_username,))
        user = cursor.fetchone()

        if not user:
            cursor.close()
            conn.close()
            return jsonify({"error": "User not found"}), 404

        # Delete the user
        cursor.execute("DELETE FROM users WHERE username = %s", (target_username,))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"message": f"User '{target_username}' removed successfully"}), 200

    except Exception as e:
        print(f"Error during user removal: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/remove_all_users", methods=["POST"])
def remove_all_users():
    """Removes all users (except admin) and clears history."""
    data = request.get_json()
    admin_username = data.get("admin_username")
    admin_password = data.get("admin_password")

    # ✅ Authenticate as admin
    if admin_username != "admin" or not authenticate_user(admin_username, admin_password):
        return jsonify({"error": "Only admin can remove all users"}), 403

    conn = get_db()
    cursor = conn.cursor()

    try:
        # ✅ Move all non-admin users to `removed_users`
        cursor.execute("""
            INSERT INTO removed_users (username, removed_at)
            SELECT username, CURRENT_TIMESTAMP FROM users WHERE username != 'admin'
        """)

        # ✅ Delete all non-admin users
        cursor.execute("DELETE FROM users WHERE username != 'admin'")

        # ✅ Clear extraction history
        cursor.execute("DELETE FROM extraction_history")

        conn.commit()
        return jsonify({"message": "All users and history removed successfully, except admin"}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": f"Failed to remove users: {str(e)}"}), 500

    finally:
        conn.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)