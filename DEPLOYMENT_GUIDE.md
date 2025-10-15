# PsySuite Web Manager - Deployment Guide

## Overview

This guide covers multiple deployment options for the PsySuite Web Manager, with specific focus on deploying to Aruba hosting services.

## Deployment Options

### Option 1: Docker Deployment (Recommended)
### Option 2: Traditional Web Server Deployment
### Option 3: Cloud/VPS Deployment

---

## Option 1: Docker Deployment (Recommended)

Docker provides the easiest and most reliable deployment method. Your project already includes complete Docker configuration.

### 1.1 Local Docker Testing

First, test the deployment locally:

```bash
cd psysuite_web

# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

This will start:
- **Web Application** on port 5000
- **PostgreSQL Database** 
- **Nginx Reverse Proxy** on ports 80/443

### 1.2 Production Docker Deployment

For production deployment, you need to:

#### A. Update Environment Variables

Create a production environment file:

```bash
# Create .env.production
cat > .env.production << 'EOF'
FLASK_CONFIG=production
DATABASE_URL=postgresql://psysuite:YOUR_SECURE_PASSWORD@db:5432/psysuite_web
SECRET_KEY=YOUR_VERY_SECURE_SECRET_KEY_CHANGE_THIS_NOW
MAIL_SERVER=smtp.your-provider.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@domain.com
MAIL_PASSWORD=your-email-password
EOF
```

#### B. Update docker-compose.yml for Production

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    env_file:
      - .env.production
    depends_on:
      - db
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=psysuite_web
      - POSTGRES_USER=psysuite
      - POSTGRES_PASSWORD=YOUR_SECURE_PASSWORD  # Change this!
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl  # For HTTPS certificates
    depends_on:
      - web
    restart: unless-stopped

volumes:
  postgres_data:
```

### 1.3 Aruba Hosting with Docker

If Aruba supports Docker (VPS/Cloud servers):

```bash
# 1. Upload your project to the server
scp -r psysuite_web/ user@your-server.aruba.it:/home/user/

# 2. SSH into your server
ssh user@your-server.aruba.it

# 3. Install Docker and Docker Compose
sudo apt update
sudo apt install docker.io docker-compose

# 4. Navigate to project and deploy
cd psysuite_web
sudo docker-compose up -d --build

# 5. Initialize database
sudo docker-compose exec web python init_db.py
```

---

## Option 2: Traditional Web Server Deployment

If Aruba doesn't support Docker, you can deploy traditionally with Apache/Nginx + Python.

### 2.1 Server Requirements

```bash
# Install required packages
sudo apt update
sudo apt install python3 python3-pip python3-venv nginx postgresql postgresql-contrib
```

### 2.2 Database Setup

```bash
# Setup PostgreSQL
sudo -u postgres psql

-- In PostgreSQL console:
CREATE DATABASE psysuite_web;
CREATE USER psysuite WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE psysuite_web TO psysuite;
\q
```

### 2.3 Application Setup

```bash
# Create application directory
sudo mkdir -p /var/www/psysuite
sudo chown $USER:$USER /var/www/psysuite

# Copy your application
cp -r psysuite_web/* /var/www/psysuite/

# Setup Python environment
cd /var/www/psysuite
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup environment variables
cat > .env << 'EOF'
FLASK_CONFIG=production
DATABASE_URL=postgresql://psysuite:your_secure_password@localhost:5432/psysuite_web
SECRET_KEY=your-very-secure-secret-key
EOF

# Initialize database
python init_db.py

# Test the application
python run.py
```

### 2.4 Nginx Configuration

Create `/etc/nginx/sites-available/psysuite`:

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /var/www/psysuite/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/psysuite /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 2.5 Systemd Service

Create `/etc/systemd/system/psysuite.service`:

```ini
[Unit]
Description=PsySuite Web Manager
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/psysuite
Environment=PATH=/var/www/psysuite/venv/bin
ExecStart=/var/www/psysuite/venv/bin/python run.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable psysuite
sudo systemctl start psysuite
```

---

## Option 3: Aruba Shared Hosting

If you're using Aruba's shared hosting (not VPS), you'll need to adapt the deployment.

### 3.1 Check Aruba Capabilities

First, check what Aruba supports:
- Python version (3.7+ required)
- Database options (MySQL/PostgreSQL)
- Process management
- Custom domains

### 3.2 Shared Hosting Deployment

```bash
# 1. Modify for shared hosting constraints
# Update config.py to use SQLite if PostgreSQL not available

class ProductionConfig(Config):
    # Use SQLite for shared hosting
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'psysuite.db')
```

### 3.3 Upload via FTP/SFTP

```bash
# Upload files to your Aruba web directory
# Usually something like: /public_html/ or /www/

# Install dependencies (if pip is available)
pip3 install --user -r requirements.txt

# Initialize database
python3 init_db.py

# Start application (method depends on Aruba's setup)
python3 run.py
```

---

## SSL/HTTPS Setup

### For Docker Deployment

1. **Get SSL Certificate** (Let's Encrypt recommended):

```bash
# Install certbot
sudo apt install certbot

# Get certificate
sudo certbot certonly --standalone -d your-domain.com

# Copy certificates to project
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem psysuite_web/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem psysuite_web/ssl/
```

2. **Update nginx.conf** for HTTPS:

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;

    location / {
        proxy_pass http://web:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

---

## Monitoring and Maintenance

### Health Checks

The application includes health check endpoints:

```bash
# Check application health
curl http://your-domain.com/api/health

# Check database connectivity
curl http://your-domain.com/api/health/db
```

### Logs

```bash
# Docker logs
docker-compose logs -f web

# Traditional deployment logs
tail -f /var/www/psysuite/logs/app.log
```

### Backup

```bash
# Database backup (PostgreSQL)
pg_dump -h localhost -U psysuite psysuite_web > backup_$(date +%Y%m%d).sql

# Docker database backup
docker-compose exec db pg_dump -U psysuite psysuite_web > backup_$(date +%Y%m%d).sql
```

---

## Aruba-Specific Instructions

### For Aruba Cloud/VPS

1. **Order VPS** with Ubuntu 20.04+
2. **Use Docker deployment** (Option 1) - most reliable
3. **Configure firewall** to allow ports 80, 443, 22
4. **Setup domain** pointing to your VPS IP

### For Aruba Shared Hosting

1. **Check Python support** in your hosting panel
2. **Use SQLite database** instead of PostgreSQL
3. **Upload via FTP/SFTP** to public_html
4. **Configure through hosting panel**

### Domain Configuration

In your Aruba domain panel:
- **A Record**: `@` → `YOUR_SERVER_IP`
- **A Record**: `www` → `YOUR_SERVER_IP`
- **CNAME**: `api` → `your-domain.com` (optional)

---

## Quick Start Commands

### Docker Deployment (Recommended)

```bash
# 1. Clone/upload project to server
cd psysuite_web

# 2. Update environment variables
cp .env.example .env
nano .env  # Edit with your settings

# 3. Deploy
docker-compose up -d --build

# 4. Initialize database
docker-compose exec web python init_db.py

# 5. Check status
docker-compose ps
curl http://localhost/api/health
```

### Traditional Deployment

```bash
# 1. Setup environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Configure database
export DATABASE_URL="postgresql://user:pass@localhost/psysuite_web"
export SECRET_KEY="your-secret-key"

# 3. Initialize and run
python init_db.py
python run.py
```

---

## Troubleshooting

### Common Issues

**Port already in use:**
```bash
sudo lsof -i :5000
sudo kill -9 PID
```

**Database connection failed:**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check connection
psql -h localhost -U psysuite -d psysuite_web
```

**Permission denied:**
```bash
sudo chown -R $USER:$USER /var/www/psysuite
chmod +x run.py
```

### Support

For Aruba-specific issues:
1. Check Aruba documentation
2. Contact Aruba support
3. Use their hosting panel tools

The Docker deployment is the most reliable option and works on most VPS providers including Aruba Cloud services.