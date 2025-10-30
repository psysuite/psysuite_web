-- SQL Script to add TestBIS test and create testbis_trials table
-- This can be run directly on any PostgreSQL database

-- Add TestBIS test to tests table (if not exists)
INSERT INTO tests (name, class_name, description, status, created_at, updated_at, trial_columns, trial_columns_order)
SELECT 
    'Temporal Bisection',
    'TestBIS',
    'this is the temporal bisection task',
    'production',
    '2000-01-01 00:00:00'::timestamp,
    NOW(),
    '{"trid": "integer", "label": "string", "lat": "integer", "confl": "string", "res": "boolean", "cor_ans": "integer", "user_ans": "integer", "elapsed": "bigint", "rep": "integer", "confl_magn": "float"}'::jsonb,
    NULL
WHERE NOT EXISTS (
    SELECT 1 FROM tests WHERE class_name = 'TestBIS'
);

-- Create testbis_trials table (if not exists)
CREATE TABLE IF NOT EXISTS testbis_trials (
    id SERIAL PRIMARY KEY,
    experiment_id INTEGER NOT NULL,
    trid INTEGER,
    created_at TIMESTAMP,
    label VARCHAR(255),
    lat INTEGER,
    confl VARCHAR(255),
    res BOOLEAN,
    cor_ans INTEGER,
    user_ans INTEGER,
    elapsed BIGINT,
    rep INTEGER,
    confl_magn DOUBLE PRECISION,
    FOREIGN KEY (experiment_id) REFERENCES experiments(id) ON DELETE CASCADE
);

-- Create index on experiment_id for better performance
CREATE INDEX IF NOT EXISTS idx_testbis_trials_experiment_id ON testbis_trials(experiment_id);

-- Display confirmation
SELECT 
    'TestBIS test and testbis_trials table setup complete!' as message,
    (SELECT COUNT(*) FROM tests WHERE class_name = 'TestBIS') as testbis_tests_count,
    (SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'testbis_trials') as testbis_trials_table_exists;
