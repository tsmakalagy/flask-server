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

        # Generate JWT
        access_token = create_access_token(identity=phone_number)
        conn.commit()

        return jsonify({"status": "success", "access_token": access_token}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cur.close()
        conn.close()