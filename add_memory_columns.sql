-- Add missing columns to production database
-- Run this SQL in your Render PostgreSQL database

-- Add global_memory to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS global_memory JSONB DEFAULT '{}' NOT NULL;

-- Add session_memory to conversations table  
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS session_memory JSONB DEFAULT '{}' NOT NULL;

-- Add is_admin to users table (if not exists)
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin VARCHAR DEFAULT 'false' NOT NULL;