# Switch to Docker environment
./deploy.sh env-docker

# Add TestBIS manually to Docker database
docker-compose exec web python -c "
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
"
