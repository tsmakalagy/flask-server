from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from utils import get_db_connection, generate_otp
import requests
from config import Config
from werkzeug.security import generate_password_hash, check_password_hash
import re
from psycopg2 import errors
from psycopg2.extras import RealDictCursor

auth = Blueprint('auth', __name__)

def check_rate_limit(identifier, ip_address):
    """Check if the login attempts exceed the rate limit."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Count failed attempts in the last 15 minutes
        cur.execute("""
            SELECT COUNT(*) FROM login_attempts 
            WHERE (email = %s OR phone_number = %s OR ip_address = %s)
            AND attempt_time > NOW() - INTERVAL '15 minutes'
            AND success = FALSE
        """, (identifier, identifier, ip_address))
        
        count = cur.fetchone()[0]
        return count < 5  # Allow up to 5 attempts per 15 minutes
    finally:
        cur.close()
        conn.close()

def log_login_attempt(identifier, ip_address, success):
    """Log the login attempt."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        is_email = '@' in identifier
        cur.execute("""
            INSERT INTO login_attempts 
            (email, phone_number, ip_address, success) 
            VALUES (%s, %s, %s, %s)
        """, (
            identifier if is_email else None,
            identifier if not is_email else None,
            ip_address,
            success
        ))
        conn.commit()
    finally:
        cur.close()
        conn.close()

@auth.route('/email/register', methods=['POST'])
def email_register():
    """Register a user with email and password."""
    data = request.json
    email = data.get("email")
    password = data.get("password")
    name = data.get("name", "")
    app_name = data.get("app_name", "Unknown App")

    if not all([email, password]):
        return jsonify({
            "status": "error",
            "message": "Email and password are required"
        }), 400

    if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
        return jsonify({
            "status": "error",
            "message": "Invalid email format"
        }), 400

    if len(password) < Config.MIN_PASSWORD_LENGTH:
        return jsonify({
            "status": "error",
            "message": f"Password must be at least {Config.MIN_PASSWORD_LENGTH} characters long"
        }), 400

    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Start transaction
                cur.execute("BEGIN")
                
                # Create new user
                cur.execute("""
                    INSERT INTO users (email, password_hash, name, auth_type)
                    VALUES (%s, %s, %s, 'email')
                    RETURNING id, email, name
                """, (email, generate_password_hash(password), name))
                
                user = cur.fetchone()
                
                # Add app to user_apps
                cur.execute("""
                    INSERT INTO user_apps (user_id, app_name)
                    VALUES (%s, %s)
                    ON CONFLICT ON CONSTRAINT user_apps_pkey DO UPDATE 
                    SET updated_at = CURRENT_TIMESTAMP
                """, (user['id'], app_name))
                
                # Create JWT token
                access_token = create_access_token(identity=user['id'])
                
                return jsonify({
                    "status": "success",
                    "message": "Registration successful",
                    "access_token": access_token,
                    "user": user
                }), 200

    except errors.UniqueViolation:
        return jsonify({
            "status": "error",
            "message": "Email already registered"
        }), 400
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    finally:
        conn.close()

@auth.route('/email/login', methods=['POST'])
def email_login():
    """Login with email and password."""
    data = request.json
    email = data.get("email")
    password = data.get("password")
    app_name = data.get("app_name", "Unknown App")
    ip_address = request.remote_addr

    if not all([email, password]):
        return jsonify({
            "status": "error",
            "message": "Email and password are required"
        }), 400

    if not check_rate_limit(email, ip_address):
        return jsonify({
            "status": "error",
            "message": "Too many login attempts. Please try again later."
        }), 429

    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, email, name, password_hash 
                    FROM users 
                    WHERE email = %s
                """, (email,))
                
                user = cur.fetchone()

                if not user or not check_password_hash(user['password_hash'], password):
                    log_login_attempt(email, ip_address, False)
                    return jsonify({
                        "status": "error",
                        "message": "Invalid email or password"
                    }), 401

                # Update user_apps
                cur.execute("""
                    INSERT INTO user_apps (user_id, app_name)
                    VALUES (%s, %s)
                    ON CONFLICT ON CONSTRAINT user_apps_pkey DO UPDATE 
                    SET updated_at = CURRENT_TIMESTAMP
                """, (user['id'], app_name))

                # Log successful login
                log_login_attempt(email, ip_address, True)

                # Generate JWT
                access_token = create_access_token(identity=user['id'])

                return jsonify({
                    "status": "success",
                    "access_token": access_token,
                    "user": {
                        "id": user['id'],
                        "email": user['email'],
                        "name": user['name']
                    }
                }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    finally:
        conn.close()

@auth.route('/register', methods=['POST'])
def register():
    """Register a user and send an OTP."""
    data = request.json
    phone_number = data.get("phone_number")
    name = data.get("name", "")
    app_name = data.get("app_name", "Unknown App")

    if not phone_number:
        return jsonify({"status": "error", "message": "Phone number is required"}), 400

    otp = generate_otp()

    try:
        # Save OTP to the database
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO sms_logs (phone_number, otp, verified) VALUES (%s, %s, %s)",
            (phone_number, otp, False)
        )
        conn.commit()

        # Send OTP via SMS Gateway
        response = requests.post(Config.SMS_GATEWAY_URL, json={"phone_number": phone_number, "message": f"Your OTP is {otp}"})
        if response.status_code != 200:
            return jsonify({"status": "error", "message": "Failed to send OTP"}), 500

        return jsonify({"status": "success", "message": "OTP sent successfully"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cur.close()
        conn.close()

@auth.route('/verify-otp', methods=['POST'])
def verify_otp():
    """Verify the OTP and issue a JWT."""
    data = request.json
    phone_number = data.get("phone_number")
    otp = data.get("otp")
    name = data.get("name", "Unknown")  # Optional name field
    app_name = data.get("app_name", "Unknown App")

    if not phone_number or not otp:
        return jsonify({"status": "error", "message": "Phone number and OTP are required"}), 400

    try:
        # Validate OTP
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM sms_logs WHERE phone_number = %s AND otp = %s AND verified = FALSE",
            (phone_number, otp)
        )
        record = cur.fetchone()

        if not record:
            return jsonify({"status": "error", "message": "Invalid or expired OTP"}), 400

        # Mark OTP as verified
        cur.execute(
            "UPDATE sms_logs SET verified = TRUE WHERE phone_number = %s AND otp = %s",
            (phone_number, otp)
        )

        # Add app to `user_apps` table if not already present
        cur.execute(
            "SELECT id FROM users WHERE phone_number = %s",
            (phone_number,)
        )
        user_record = cur.fetchone()
        
        if user_record is None:
            # Create new user
            cur.execute(
                "INSERT INTO users (phone_number, name) VALUES (%s, %s) RETURNING id",
                (phone_number, name)
            )
            user_id = cur.fetchone()[0]
        else:
            user_id = user_record[0]

        # Add app to user_apps table
        cur.execute(
            """
            INSERT INTO user_apps (user_id, app_name)
            VALUES (%s, %s)
            ON CONFLICT ON CONSTRAINT user_apps_pkey DO UPDATE 
            SET created_at = CURRENT_TIMESTAMP
            """,
            (user_id, app_name)
        )

        # Generate JWT
        access_token = create_access_token(identity=user_id)
        conn.commit()

        return jsonify({"status": "success", "access_token": access_token}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cur.close()
        conn.close()