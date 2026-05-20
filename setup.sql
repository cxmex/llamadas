-- Run this in Supabase SQL Editor
-- https://supabase.com/dashboard/project/gbkhkbfbarsnpbdkxzii/sql

CREATE TABLE IF NOT EXISTS crm_users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS crm_contacts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(50) NOT NULL,
    imported_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS crm_call_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES crm_users(id) NOT NULL,
    contact_id INTEGER REFERENCES crm_contacts(id) NOT NULL,
    status VARCHAR(50) NOT NULL,
    notes TEXT DEFAULT '',
    interested BOOLEAN DEFAULT FALSE,
    callback_date VARCHAR(50),
    completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, contact_id)
);

-- Enable RLS but allow all access with anon key (simple setup)
ALTER TABLE crm_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE crm_contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE crm_call_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all on crm_users" ON crm_users FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all on crm_contacts" ON crm_contacts FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all on crm_call_logs" ON crm_call_logs FOR ALL USING (true) WITH CHECK (true);
