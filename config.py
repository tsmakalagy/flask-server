import os

class Config:
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your_jwt_secret_key")
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/dbname")
    SMS_GATEWAY_URL = os.getenv("SMS_GATEWAY_URL", "http://127.0.0.1:5001/send-sms")
    JWT_ACCESS_TOKEN_EXPIRES = 30 * 24 * 3600
    MIN_PASSWORD_LENGTH = 6