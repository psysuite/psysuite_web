#!/bin/bash

echo "🚀 Setting up production database..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker containers are running
if ! docker-compose ps | grep -q "web_app_web_1.*Up"; then
    print_error "Docker containers are not running. Please run 'bash deploy.sh docker' first."
    exit 1
fi

# Ensure we're using Docker environment
if [ -f .env.docker ]; then
    print_status "Ensuring Docker environment is active..."
    cp .env.docker .env
else
    print_error ".env.docker file not found. Please run 'bash deploy.sh docker' first."
    exit 1
fi

# Recreate database using the working init_db.py approach, adds one admin user
print_status "Recreating database..."
docker-compose exec -T web python init_db.py

# Add TestBIS test
print_status "Adding TestBIS test..."
docker-compose exec -T web bash -c "cd /app && python -c \"
import os
import sys
from datetime import datetime
from app import create_app, db
from app.models.test import Test
from sqlalchemy import text

app = create_app('production')
with app.app_context():
    # Check if TestBIS already exists
    existing_test = Test.query.filter_by(class_name='TestBIS').first()
    if existing_test:
        print('✅ TestBIS test already exists in database')
    else:
        print('📝 Creating TestBIS test...')
        testbis = Test(
            name='Temporal Bisection',
            class_name='TestBIS',
            description='this is the temporal bisection task',
            status='production',
            created_at=datetime(2000, 1, 1),
            updated_at=datetime.now(),
            _trial_columns={
                'trid': 'integer',
                'label': 'string',
                'lat': 'integer',
                'confl': 'string',
                'res': 'boolean',
                'cor_ans': 'integer',
                'user_ans': 'integer',
                'elapsed': 'bigint',
                'rep': 'integer',
                'confl_magn': 'float'
            },
            trial_columns_order=None
        )
        db.session.add(testbis)
        db.session.commit()
        print('✅ TestBIS test created successfully')
        
    # Create testbis_trials table
    inspector = db.inspect(db.engine)
    if 'testbis_trials' in inspector.get_table_names():
        print('✅ testbis_trials table already exists')
    else:
        print('📝 Creating testbis_trials table...')
        create_table_sql = '''
        CREATE TABLE testbis_trials (
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
        '''
        db.session.execute(text(create_table_sql))
        db.session.commit()
        print('✅ testbis_trials table created successfully')
        
    print('🎉 TestBIS setup complete!')
\""

print_status "✅ Production database setup complete!"
print_status "🌐 Your application should be accessible at: http://localhost"