from utils import get_db_connection

def init_db():
    """Initialize database schema."""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Create tables
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        phone_number TEXT NOT NULL UNIQUE,
        name TEXT,
        created_at TIMESTAMP DEFAULT now()
    );
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sms_logs (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        phone_number TEXT NOT NULL,
        otp TEXT NOT NULL,
        sent_at TIMESTAMP DEFAULT now(),
        verified BOOLEAN DEFAULT FALSE
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_apps (
        user_id UUID REFERENCES users(id),
        app_name VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT user_apps_pkey PRIMARY KEY (user_id, app_name)
    );
    """)

    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    init_db()