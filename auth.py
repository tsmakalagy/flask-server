from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from utils import get_db_connection, generate_otp
import requests
from config import Config

auth = Blueprint('auth', __name__)

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