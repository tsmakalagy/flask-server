-- Add timestamp columns to user_apps table
ALTER TABLE user_apps
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;

-- Create or replace the update trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add trigger to user_apps table
DROP TRIGGER IF EXISTS update_user_apps_updated_at ON user_apps;
CREATE TRIGGER update_user_apps_updated_at
    BEFORE UPDATE ON user_apps
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();