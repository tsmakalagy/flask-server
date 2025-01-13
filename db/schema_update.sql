-- First, drop the not-null constraint from phone_number
ALTER TABLE users 
ALTER COLUMN phone_number DROP NOT NULL;

-- Add constraint to ensure either email or phone_number is present
ALTER TABLE users
ADD CONSTRAINT user_contact_info_check 
CHECK (
    (auth_type = 'email' AND email IS NOT NULL) 
    OR 
    (auth_type = 'phone' AND phone_number IS NOT NULL)
);

-- Update indexes to handle nullable columns
DROP INDEX IF EXISTS unique_phone_number_idx;
DROP INDEX IF EXISTS unique_email_idx;

CREATE UNIQUE INDEX unique_phone_number_idx 
ON users (phone_number) 
WHERE phone_number IS NOT NULL;

CREATE UNIQUE INDEX unique_email_idx 
ON users (email) 
WHERE email IS NOT NULL;