# PsySuite Web Manager - Complete Developer Guide

**Last Updated**: March 2026  
**For**: All development scenarios - local venv, local Docker, remote VPS

---

## Quick Command Reference by Scenario

| Scenario | First Installation | Start Environment | Code Changes | DB Reset | DB Backup |
|----------|-------------------|-------------------|--------------|----------|-----------|
| **venv (local)** | `python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && python scripts/db/dev_recreate_db.py` | `python scripts/run_debug.py` | Restart server (Ctrl+C, then run again) | `python scripts/db/dev_recreate_db.py` | `pg_dump -U psysuite_user -d psysuite_dev > backup.sql` |
| **Docker (local)** | `./deploy.sh docker && ./scripts/db/prod_add_testbis.sh` | `docker-compose up -d` | `docker-compose down && docker-compose up -d --build` | `./scripts/db/prod_recreate_db.sh` | `docker-compose exec db pg_dump -U psysuite psysuite_web > backup.sql` |
| **Docker (VPS)** | `git init && git remote add origin <url> && git pull origin main && ./deploy.sh docker` | `docker-compose up -d` | `git pull origin main && docker-compose down && docker-compose up -d --build` | `./scripts/db/prod_recreate_db.sh` | `docker-compose exec db pg_dump -U psysuite psysuite_web > backup.sql` |

---

## Table of Contents

1. [Scenario 1: Local Development (venv)](#scenario-1-local-development-venv)
2. [Scenario 2: Local Docker](#scenario-2-local-docker)
3. [Scenario 3: Remote VPS](#scenario-3-remote-vps)
4. [Database Management](#database-management)
5. [Code Updates & Deployment](#code-updates--deployment)
6. [Troubleshooting](#troubleshooting)

---

## Scenario 1: Local Development (venv)

### First Installation

```bash
cd web_app

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Setup database
python scripts/db/dev_recreate_db.py

# Start server
python scripts/run_debug.py
```

**Access**: http://localhost:5001  
**Login**: XXXXXXX / YYYYYY

### Database Operations

#### Connect to Database
```bash
psql -U psysuite_user -d psysuite_dev -h localhost
```

#### Reset Database
```bash
python scripts/db/dev_recreate_db.py
```

#### Add TestBIS Test
```bash
python scripts/db/dev_add_testbis.py
```

#### Backup Database
```bash
pg_dump -U psysuite_user -d psysuite_dev -h localhost > backup_$(date +%Y%m%d).sql
```

#### Restore Database
```bash
psql -U psysuite_user -d psysuite_dev -h localhost < backup.sql
```

### Common SQL Operations

```sql
-- View experiments
SELECT id, exp_uid, label, age, uploaded_at FROM experiments ORDER BY uploaded_at DESC;

-- Delete experiment
DELETE FROM experiments WHERE id = 123;

-- Delete by subject
DELETE FROM experiments WHERE label = 'Subject_001';

-- Delete old data
DELETE FROM experiments WHERE uploaded_at < NOW() - INTERVAL '30 days';

-- Count experiments
SELECT COUNT(*) FROM experiments;

-- View users
SELECT id, email, role FROM users;

-- Add admin user
INSERT INTO users (email, role, password_hash, created_at)
VALUES ('admin@example.com', 'admin', 'hash', NOW());

-- Change user role
UPDATE users SET role = 'admin' WHERE email = 'user@example.com';
```

### Python Console Operations

```bash
python

from app import create_app, db
from app.models.experiment import Experiment
from app.models.user import User

app = create_app('development')
with app.app_context():
    # Delete experiment
    exp = Experiment.query.get(123)
    if exp:
        db.session.delete(exp)
        db.session.commit()
        print("Deleted")
    
    # List experiments
    experiments = Experiment.query.all()
    for exp in experiments:
        print(f"{exp.id}: {exp.label}")
    
    # Add admin user
    new_user = User(email='admin@example.com', role='admin')
    new_user.set_password('password')
    db.session.add(new_user)
    db.session.commit()
    print("User created")
```

### Restart Server

```bash
# Stop: Ctrl+C
# Start: python scripts/run_debug.py
```

### Code Changes (without touching DB)

Just restart the server - code changes are picked up automatically:

```bash
# Stop: Ctrl+C
# Start: python scripts/run_debug.py
```

---

## Scenario 2: Local Docker

### First Installation

```bash
cd web_app

# Deploy with Docker
./deploy.sh docker

# Add test data
./scripts/db/prod_add_testbis.sh
```

**Access**: http://localhost  
**Login**: XXXXXXX / YYYYYY

### Database Operations

#### Connect to Database
```bash
docker-compose exec db psql -U psysuite -d psysuite_web
```

#### Reset Database
```bash
./scripts/db/prod_recreate_db.sh
```

#### Add TestBIS Test
```bash
./scripts/db/prod_add_testbis.sh
```

#### Backup Database
```bash
docker-compose exec db pg_dump -U psysuite psysuite_web > backup_$(date +%Y%m%d).sql
```

#### Restore Database
```bash
docker-compose exec db psql -U psysuite psysuite_web < backup.sql
```

### Common SQL Operations

```sql
-- View experiments
SELECT id, exp_uid, label, age, uploaded_at FROM experiments ORDER BY uploaded_at DESC;

-- Delete experiment
DELETE FROM experiments WHERE id = 123;

-- Delete by subject
DELETE FROM experiments WHERE label = 'Subject_001';

-- Delete old data
DELETE FROM experiments WHERE uploaded_at < NOW() - INTERVAL '30 days';

-- Count experiments
SELECT COUNT(*) FROM experiments;

-- View users
SELECT id, email, role FROM users;

-- Add admin user
INSERT INTO users (email, role, password_hash, created_at)
VALUES ('admin@example.com', 'admin', 'hash', NOW());

-- Change user role
UPDATE users SET role = 'admin' WHERE email = 'user@example.com';
```

### Python Console Operations

```bash
docker-compose exec web python

from app import create_app, db
from app.models.experiment import Experiment
from app.models.user import User

app = create_app('production')
with app.app_context():
    # Delete experiment
    exp = Experiment.query.get(123)
    if exp:
        db.session.delete(exp)
        db.session.commit()
        print("Deleted")
    
    # List experiments
    experiments = Experiment.query.all()
    for exp in experiments:
        print(f"{exp.id}: {exp.label}")
    
    # Add admin user
    new_user = User(email='admin@example.com', role='admin')
    new_user.set_password('password')
    db.session.add(new_user)
    db.session.commit()
    print("User created")
```

### Check Status

```bash
# Check containers
docker-compose ps

# View logs
docker-compose logs -f web

# Health check
curl http://localhost/api/health
```

### Restart Application

```bash
# Restart specific service
docker-compose restart web

# Full restart
docker-compose down
docker-compose up -d
```

### Code Changes (without touching DB)

**If only Python/HTML code changed**:
```bash
docker-compose restart web
```

**If changes don't appear or dependencies changed**:
```bash
docker-compose down
docker-compose up -d --build
```

**If still not working (clear Docker cache)**:
```bash
docker system prune -a
docker-compose down
docker-compose up -d
```

---

## Scenario 3: Remote VPS

### First Installation

```bash
# From local machine
scp -r web_app/ root@your-vps-ip:/root/

# SSH to VPS
ssh root@your-vps-ip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
apt install docker-compose

# Deploy
cd /root/web_app
./deploy.sh docker

# Add test data
./scripts/db/prod_add_testbis.sh
```

**Access**: http://your-domain.com  
**Login**: XXXXXXX / YYYYYY

### Initialize Git (Connect Existing VPS)

If you already have a running VPS with data:

```bash
# On VPS
cd /root/web_app

# Initialize Git
git init
git remote add origin https://github.com/your-username/web_app.git
git config user.name "Your Name"
git config user.email "your-email@example.com"

# Pull code (database stays intact!)
git pull origin main

# Start containers if not running
docker-compose up -d
```

### Database Operations

#### Connect to Database
```bash
docker-compose exec db psql -U psysuite -d psysuite_web
```

#### Reset Database
```bash
./scripts/db/prod_recreate_db.sh
```

#### Add TestBIS Test
```bash
./scripts/db/prod_add_testbis.sh
```

#### Backup Database
```bash
docker-compose exec db pg_dump -U psysuite psysuite_web > backup_$(date +%Y%m%d).sql

# Download to local machine
scp root@your-vps-ip:/root/web_app/backup_*.sql ./
```

#### Restore Database
```bash
docker-compose exec db psql -U psysuite psysuite_web < backup.sql
```

### Common SQL Operations

```sql
-- View experiments
SELECT id, exp_uid, label, age, uploaded_at FROM experiments ORDER BY uploaded_at DESC;

-- Delete experiment
DELETE FROM experiments WHERE id = 123;

-- Delete by subject
DELETE FROM experiments WHERE label = 'Subject_001';

-- Delete old data
DELETE FROM experiments WHERE uploaded_at < NOW() - INTERVAL '30 days';

-- Count experiments
SELECT COUNT(*) FROM experiments;

-- View users
SELECT id, email, role FROM users;

-- Add admin user
INSERT INTO users (email, role, password_hash, created_at)
VALUES ('admin@example.com', 'admin', 'hash', NOW());

-- Change user role
UPDATE users SET role = 'admin' WHERE email = 'user@example.com';
```

### Python Console Operations

```bash
docker-compose exec web python

from app import create_app, db
from app.models.experiment import Experiment
from app.models.user import User

app = create_app('production')
with app.app_context():
    # Delete experiment
    exp = Experiment.query.get(123)
    if exp:
        db.session.delete(exp)
        db.session.commit()
        print("Deleted")
    
    # List experiments
    experiments = Experiment.query.all()
    for exp in experiments:
        print(f"{exp.id}: {exp.label}")
    
    # Add admin user
    new_user = User(email='admin@example.com', role='admin')
    new_user.set_password('password')
    db.session.add(new_user)
    db.session.commit()
    print("User created")
```

### Check Status

```bash
# Check containers
docker-compose ps

# View logs
docker-compose logs -f web

# Health check
curl http://localhost/api/health
```

### Restart Application

```bash
# Restart specific service
docker-compose restart web

# Full restart
docker-compose down
docker-compose up -d
```

### Code Changes (without touching DB)

**If only Python/HTML code changed**:
```bash
# Pull latest code
git pull origin main

# Restart containers
docker-compose restart web
```

**If changes don't appear or dependencies changed**:
```bash
# Pull latest code
git pull origin main

# Rebuild
docker-compose down
docker-compose up -d --build
```

**If still not working (clear Docker cache)**:
```bash
git pull origin main
docker system prune -a
docker-compose down
docker-compose up -d
```

---

## Database Management

### Backup & Restore

#### Local (venv)
```bash
# Backup
pg_dump -U psysuite_user -d psysuite_dev -h localhost > backup.sql

# Restore
psql -U psysuite_user -d psysuite_dev -h localhost < backup.sql
```

#### Docker/VPS
```bash
# Backup
docker-compose exec db pg_dump -U psysuite psysuite_web > backup.sql

# Restore
docker-compose exec db psql -U psysuite psysuite_web < backup.sql
```

### Export/Import Data

#### Export to CSV
```bash
# Local
psql -U psysuite_user -d psysuite_dev -h localhost
\copy (SELECT id, exp_uid, label, age, uploaded_at FROM experiments) TO '/tmp/experiments.csv' WITH CSV HEADER;

# Docker/VPS
docker-compose exec db psql -U psysuite -d psysuite_web
\copy (SELECT id, exp_uid, label, age, uploaded_at FROM experiments) TO '/tmp/experiments.csv' WITH CSV HEADER;
```

#### Export via Python
```python
import csv
from app import create_app, db
from app.models.experiment import Experiment

app = create_app('development')  # or 'production'
with app.app_context():
    experiments = Experiment.query.all()
    
    with open('experiments.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'UID', 'Label', 'Age', 'Uploaded'])
        
        for exp in experiments:
            writer.writerow([exp.id, exp.exp_uid, exp.label, exp.age, exp.uploaded_at])
    
    print(f"Exported {len(experiments)} experiments")
```

---

## Code Updates & Deployment

### Local Development (venv)

**Only code changes (no DB changes)**:
```bash
# Stop server
# Ctrl+C

# Make your code changes
# ...

# Restart server
python scripts/run_debug.py
```

**With database changes**:
```bash
# Stop server (Ctrl+C)

# Make changes
# ...

# Reset database
python scripts/db/dev_recreate_db.py

# Restart server
python scripts/run_debug.py
```

### Local Docker

**Only code changes (no DB changes)**:
```bash
# Option 1: Quick restart (if only Python/HTML changed)
docker-compose restart web

# Option 2: Full rebuild (if dependencies changed)
docker-compose down
docker-compose up -d --build
```

**With database changes**:
```bash
# Reset database
./scripts/db/prod_recreate_db.sh

# Restart containers
docker-compose restart
```

**If changes don't appear**:
```bash
# Complete rebuild (clears Docker cache)
docker-compose down
docker-compose up -d --build

# Or full cleanup
docker system prune -a
docker-compose down
docker-compose up -d
```

### Remote VPS (with Git)

**Only code changes (no DB changes)**:
```bash
# Local: commit and push
git add .
git commit -m "Fix: description of change"
git push origin main

# VPS: pull and rebuild
git pull origin main
docker-compose down
docker-compose up -d --build

# Verify
docker-compose logs -f web
```

**With database changes**:
```bash
# Local: commit and push
git add .
git commit -m "Feature: description"
git push origin main

# VPS: pull, reset DB, rebuild
git pull origin main
./scripts/db/prod_recreate_db.sh
docker-compose down
docker-compose up -d --build
```

### Remote VPS (without Git)

**Only code changes (no DB changes)**:
```bash
# Local: upload new code
scp -r web_app/ root@your-vps-ip:/root/

# VPS: rebuild
docker-compose down
docker-compose up -d --build
```

**With database changes**:
```bash
# Local: upload new code
scp -r web_app/ root@your-vps-ip:/root/

# VPS: reset DB and rebuild
./scripts/db/prod_recreate_db.sh
docker-compose down
docker-compose up -d --build
```

---

## Troubleshooting

### Database Connection Refused

**Local (venv)**:
```bash
# Check PostgreSQL
sudo systemctl status postgresql

# Start PostgreSQL
sudo systemctl start postgresql

# Test connection
psql -U psysuite_user -d psysuite_dev -h localhost
```

**Docker/VPS**:
```bash
# Check containers
docker-compose ps

# Start containers
docker-compose up -d

# Check database logs
docker-compose logs db
```

### Port Already in Use

```bash
# Find process
lsof -i :5001

# Kill process
kill -9 <PID>
```

### Docker Won't Start

```bash
# Check logs
docker-compose logs

# Complete cleanup
docker-compose down
docker volume rm web_app_postgres_data

# Redeploy
./deploy.sh docker
```

### Can't Login

```bash
# Local (venv)
python scripts/db/dev_recreate_db.py

# Docker/VPS
./scripts/db/prod_recreate_db.sh
```

### Application Slow

```bash
# Check resource usage
docker stats

# Check logs
docker-compose logs web

# Restart
docker-compose restart web
```

---

## Quick Reference

| Task | venv | Docker/VPS |
|------|------|-----------|
| **Start** | `python scripts/run_debug.py` | `docker-compose up -d` |
| **Stop** | Ctrl+C | `docker-compose down` |
| **Logs** | Terminal | `docker-compose logs -f web` |
| **DB Connect** | `psql -U psysuite_user -d psysuite_dev -h localhost` | `docker-compose exec db psql -U psysuite -d psysuite_web` |
| **DB Backup** | `pg_dump -U psysuite_user -d psysuite_dev > backup.sql` | `docker-compose exec db pg_dump -U psysuite psysuite_web > backup.sql` |
| **DB Reset** | `python scripts/db/dev_recreate_db.py` | `./scripts/db/prod_recreate_db.sh` |
| **Recompile** | Restart server | `docker-compose down && docker-compose up -d --build` |
| **Health** | `curl http://localhost:5001/api/health` | `curl http://localhost/api/health` |

---

## Available Scripts

### Database Scripts

```bash
# Initialize database (fresh setup)
python scripts/db/init_db.py

# Clear all data (keep schema)
python scripts/db/dev_clear_db.py

# Recreate database from scratch
python scripts/db/dev_recreate_db.py

# Export data to JSON
python scripts/db/dev_export_data.py backup.json

# Import data from JSON
python scripts/db/dev_import_data.py backup.json
```

### Development Server

```bash
# Run debug server (PyCharm compatible)
python scripts/run_debug.py
```

### Testing

```bash
# Run all tests with coverage
python scripts/tests/run_tests.py

# Run system integration tests
python scripts/tests/test_system.py

# Test against specific URL
python scripts/tests/test_system.py https://your-domain.com
```

### Convenient Runner

```bash
# Show all options
python scripts/run.py --help

# Recreate database
python scripts/run.py db recreate

# Clear database
python scripts/run.py db clear

# Run all tests
python scripts/run.py test all

# Run system tests
python scripts/run.py test system

# Start debug server
python scripts/run.py debug
```

### Cleanup Scripts

```bash
# Complete Docker cleanup (removes everything)
./scripts/docker-cleanup.sh

# Development cleanup (removes venv + dev database)
./scripts/dev-cleanup.sh

# VPS cleanup
./scripts/cleanup_vps.sh
```

---

## Key Files

| File | Purpose |
|------|---------|
| `deploy.sh` | Main deployment script |
| `docker-compose.yml` | Docker configuration |
| `requirements.txt` | Python dependencies |
| `.env.development` | Local config |
| `.env.docker` | Production config |
| `scripts/db/` | Database management scripts |
| `scripts/run_debug.py` | Debug server |
| `scripts/docker-cleanup.sh` | Docker cleanup |
| `scripts/dev-cleanup.sh` | Development cleanup |

---

## Important Notes

1. **Always backup before major operations**: `pg_dump` before deleting data
2. **Change default passwords in production**: Don't use 'YYYYYY' on VPS
3. **Use SSH tunnels for remote DB access**: More secure than opening firewall
4. **Keep .env files secure**: Never commit to git
5. **Test locally first**: Before deploying to VPS
6. **Monitor logs**: Check `docker-compose logs` for errors

---

**Default Credentials**: XXXXXXX / YYYYYY  
**⚠️ Change password in production!**
