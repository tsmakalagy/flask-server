import psycopg2
from config import Config
import random

def get_db_connection():
    """Establish a database connection."""
    return psycopg2.connect(Config.DATABASE_URL)

def generate_otp():
    """Generate a 6-digit OTP."""
    return str(random.randint(100000, 999999))