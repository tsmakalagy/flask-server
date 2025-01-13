-- Create enum type for authentication methods
DO $$ BEGIN
    CREATE TYPE auth_type AS ENUM ('email', 'phone');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Modify users table
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS email VARCHAR(255),
ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255),
ADD COLUMN IF NOT EXISTS auth_type auth_type DEFAULT 'phone',
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;

-- Add unique constraint for email (allowing nulls)
CREATE UNIQUE INDEX IF NOT EXISTS unique_email_idx ON users (email) WHERE email IS NOT NULL;

-- Add unique constraint for phone_number (allowing nulls)
CREATE UNIQUE INDEX IF NOT EXISTS unique_phone_number_idx ON users (phone_number) WHERE phone_number IS NOT NULL;

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_users_updated_at ON users;

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create or update user_apps table if not exists
CREATE TABLE IF NOT EXISTS user_apps (
    user_id INTEGER REFERENCES users(id),
    app_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, app_name)
);

-- Create trigger for user_apps updated_at
DROP TRIGGER IF EXISTS update_user_apps_updated_at ON user_apps;

CREATE TRIGGER update_user_apps_updated_at
    BEFORE UPDATE ON user_apps
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create table for failed login attempts (for rate limiting)
CREATE TABLE IF NOT EXISTS login_attempts (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255),
    phone_number VARCHAR(50),
    ip_address INET,
    attempt_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN DEFAULT FALSE
);

-- Create index for querying recent login attempts
CREATE INDEX IF NOT EXISTS idx_login_attempts_time 
ON login_attempts (attempt_time);
CREATE INDEX IF NOT EXISTS idx_login_attempts_email 
ON login_attempts (email) WHERE email IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_login_attempts_phone 
ON login_attempts (phone_number) WHERE phone_number IS NOT NULL;

-- Update existing users to have auth_type
UPDATE users 
SET auth_type = 'phone' 
WHERE auth_type IS NULL AND phone_number IS NOT NULL;

-- Create function to clean up old login attempts
CREATE OR REPLACE FUNCTION cleanup_old_login_attempts()
RETURNS void AS $$
BEGIN
    DELETE FROM login_attempts 
    WHERE attempt_time < NOW() - INTERVAL '24 hours';
END;
$$ LANGUAGE plpgsql;

-- Optional: Create a scheduled job to clean up old login attempts
-- Requires pg_cron extension
-- SELECT cron.schedule('0 0 * * *', 'SELECT cleanup_old_login_attempts();');