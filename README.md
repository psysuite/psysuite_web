# PsySuite Web Manager

A comprehensive web-based management system for PsySuite psychophysics test data. This system provides a secure web application that allows researchers and administrators to manage tests, view results, and download data with seamless Android app integration.

## 🚀 Quick Start - Three Deployment Scenarios

### **Scenario 1: Local Development (PyCharm)**
```bash
bash scripts/dev-cleanup.sh
./deploy.sh traditional
python scripts/db/dev_add_testbis.py
# Access: http://localhost:5001
```

### **Scenario 2: Local Production (Docker)**
```bash
bash scripts/dev-cleanup.sh
./deploy.sh docker
./scripts/db/prod_add_testbis.sh
# Access: http://localhost:5000
```

### **Scenario 3: Remote Production (VPS)**
```bash
# On your VPS
./deploy.sh traditional
python scripts/db/dev_add_testbis.py
# Configure reverse proxy for HTTPS
```

## ✨ Features

- **🔐 Role-based Access Control**: Admin and researcher roles with appropriate permissions
- **🧪 Dynamic Test Management**: Automatic trial table creation and management
- **📊 Real-time Data Upload**: Robust experiment data upload from Android app
- **📈 Data Visualization**: View and analyze experiment results through web interface
- **📥 Data Export**: Download experiment data as tab-separated files or ZIP archives
- **👥 User Management**: Admin interface for managing researcher accounts and project assignments
- **🔄 Offline Support**: Android app can work offline and sync data when connection is available
- **📝 Comprehensive Logging**: Track all user activities and data access for audit purposes
- **🐳 Multi-Environment**: Supports development, Docker, and production deployments
- **🔧 Self-Healing**: Automatic trial model creation and database management

## 🏗️ Architecture

### **Core Components**
1. **Flask Web Backend**: RESTful API with automatic trial table management
2. **Dynamic Models System**: Self-creating trial tables based on test configurations
3. **Web Frontend**: Responsive HTML/CSS/JavaScript interface
4. **Android Integration**: Seamless data upload with offline support

### **Key Innovations**
- **Process-Safe Dynamic Models**: Trial models created on-demand across different processes
- **Automatic Database Management**: Tables created/updated automatically when tests are added
- **Environment-Agnostic Deployment**: Same codebase works in development, Docker, and production
- **PyCharm Debug Compatibility**: Works in both Run and Debug modes

## 🛠️ Installation & Deployment

### **Prerequisites**
- Python 3.7+ 
- PostgreSQL (production) or SQLite (development)
- Docker & Docker Compose (for Docker deployment)
- Git

### **Universal Deployment Script**

The `deploy.sh` script handles all deployment scenarios:

```bash
# Show current status
./deploy.sh status

# Development deployment (PyCharm compatible)
./deploy.sh traditional

# Production deployment (Docker)
./deploy.sh docker

# Switch environments
./deploy.sh env-dev     # Switch to development config
./deploy.sh env-docker  # Switch to Docker config

# Get help
./deploy.sh help
```

### **Environment Configuration**

The system uses environment-specific configuration files:

- **`.env.development`** - PyCharm/local development
- **`.env.docker`** - Docker production
- **`.env.production`** - VPS production

### **Default Admin Account**
- **Email**: alberto.inuggi@gmail.com  
- **Password**: antares

**⚠️ Important**: Change the default password after first login in production!

## ⚙️ Configuration

### **Automatic Database Setup**

The deployment script automatically handles database setup:

```bash
# For development (creates PostgreSQL user and database)
./deploy.sh traditional

# For Docker (uses containerized PostgreSQL)
./deploy.sh docker
```

### **Environment Files**

#### **Development (`.env.development`)**
```bash
FLASK_CONFIG=development
SECRET_KEY=psysuite-web-manager-2024-secure-key-change-in-production
DATABASE_URL=postgresql://psysuite_user:psysuite123@localhost:5432/psysuite_dev
ADMIN_EMAIL=alberto.inuggi@gmail.com
ADMIN_PASSWORD=antares
```

#### **Docker Production (`.env.docker`)**
```bash
FLASK_CONFIG=production
SECRET_KEY=your-production-secret-key
DATABASE_URL=postgresql://psysuite:psysuite_password@db:5432/psysuite_web
ADMIN_EMAIL=alberto.inuggi@gmail.com
ADMIN_PASSWORD=your-secure-password
```

#### **VPS Production (`.env.production`)**
```bash
FLASK_CONFIG=production
SECRET_KEY=your-production-secret-key
DATABASE_URL=postgresql://psysuite_user:secure_password@localhost:5432/psysuite_prod
ADMIN_EMAIL=alberto.inuggi@gmail.com
ADMIN_PASSWORD=your-secure-password
```

### **Database Requirements**

- **Development**: PostgreSQL with `psysuite_user` and `psysuite_dev` database
- **Docker**: Containerized PostgreSQL (automatically configured)
- **Production**: PostgreSQL server with appropriate user and database

## API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/me` - Get current user info
- `POST /api/auth/reset-password` - Reset password

### Test Management (Admin only)
- `GET /api/tests` - List all tests
- `POST /api/tests` - Create new test
- `GET /api/tests/{id}` - Get test details
- `PUT /api/tests/{id}` - Update test
- `DELETE /api/tests/{id}` - Delete test
- `PUT /api/tests/{id}/status` - Change test status

### User Management (Admin only)
- `GET /api/users` - List all users
- `POST /api/users` - Create new user
- `PUT /api/users/{id}` - Update user
- `DELETE /api/users/{id}` - Delete user
- `GET /api/users/{id}/tests` - Get user's assigned tests
- `PUT /api/users/{id}/tests` - Update user's test assignments

### Experiment Data
- `GET /api/experiments` - List experiments (filtered by permissions)
- `GET /api/experiments/{id}` - Get experiment details
- `GET /api/experiments/{id}/trials` - Get experiment trial data
- `GET /api/experiments/download` - Download selected experiments

### Data Upload (from Android)
- `POST /api/upload/experiment` - Upload experiment data
- `POST /api/upload/validate` - Validate experiment data
- `GET /api/upload/status` - Get upload service status

### System Health
- `GET /api/health` - Basic health check
- `GET /api/status` - Detailed system status

## 📱 Android Integration

### **Robust Upload System**

The system features a **self-healing upload mechanism** that automatically handles:
- **Missing trial models** - Created on-demand from test configuration
- **Process separation** - Works across different server processes
- **Network issues** - Offline support with automatic sync

### **Configuration**

Configure the Android app with your server URL:

```kotlin
// In ResultsManager
resultManager.setWebApiUrl("https://your-server.com")  // or http://localhost:5001 for development
resultManager.setWebUploadEnabled(true)
```

### **Upload Process**

1. **Test Completion** → Android app uploads results immediately
2. **Network Unavailable** → Results stored locally in Downloads folder  
3. **App Startup** → Automatic sync of pending uploads
4. **Success** → Files moved to private app storage
5. **Server Processing** → Automatic trial table creation if needed

### **Supported Test Types**

- **TestBIS** (Temporal Bisection) - Fully configured and tested
- **Custom Tests** - Automatic trial table creation from test configuration
- **Dynamic Columns** - Flexible trial data structure

### **Upload Data Format**

```json
{
  "exp_uid": "TestBIS1761060817710_9202f7ba",
  "test_class_name": "TestBIS", 
  "device_id": "android_device_123",
  "configuration": {
    "label": "subject_001",
    "age": 25,
    "gender": 1,
    "population": "normal",
    "session": 1,
    "type": 0,
    "project": "research_project_2024",
    "device": {...},
    "vercode": "1.0.0",
    "stimuliDelays": [400, 800, 1200],
    "whitenoise": false,
    "trman_type": "adaptive",
    "showResult": true,
    "canRepeat": false,
    "doTraining": true,
    "date": "2024-10-30"
  },
  "trials": [
    {
      "trid": 1,
      "label": "subject_001",
      "lat": 800,
      "confl": "short",
      "res": true,
      "cor_ans": 1,
      "user_ans": 1,
      "elapsed": 1250,
      "rep": 1,
      "confl_magn": 0.5
    }
  ]
}
```

## Web Interface

### Admin Features

- **Dashboard**: View all tests and their parameters
- **Test Management**: Create, edit, delete, and manage test configurations
- **User Management**: Create researcher accounts and assign test access
- **System Monitoring**: View system health and usage statistics

### Researcher Features

- **Dashboard**: View assigned tests and their parameters
- **Experiment Viewing**: Browse and search experiment data
- **Data Export**: Download experiment data as TSV files or ZIP archives
- **Trial Analysis**: View detailed trial data for individual experiments

## 🗄️ Database Schema

### **Core Tables**
- **`users`** - User accounts and roles
- **`tests`** - Test configurations with dynamic trial column definitions
- **`experiments`** - Experiment instances and subject data  
- **`projects`** - Research projects and organization
- **`project_assignments`** - User-project access permissions
- **`access_logs`** - System access and activity logging
- **`mobile_applications`** - Android app version management

### **Dynamic Trial Tables**
- **`testbis_trials`** - TestBIS trial results (automatically created)
- **`{test_class_name}_trials`** - Custom test trial results (created on-demand)

### **Automatic Table Management**
- ✅ **Trial tables created automatically** when tests are added
- ✅ **Schema updates** when test configurations change  
- ✅ **On-demand model creation** during uploads
- ✅ **Cleanup** when tests are deleted

### **Key Features**
- **Dynamic Schema**: Trial tables adapt to test configurations
- **Self-Healing**: Missing models created automatically during uploads
- **Process-Safe**: Works across different server processes and containers
- **Migration-Free**: No manual database migrations needed for trial tables

## Security

- **Authentication**: Secure password hashing with bcrypt
- **Session Management**: Flask-Login with secure session handling
- **Role-based Access**: Admin and researcher roles with appropriate permissions
- **Input Validation**: Comprehensive validation of all user inputs
- **SQL Injection Protection**: SQLAlchemy ORM with parameterized queries
- **HTTPS**: Use HTTPS in production (configure your web server)

## 🚀 Advanced Deployment

### **Production VPS Deployment**

#### **1. Server Setup**
```bash
# Install dependencies
sudo apt update
sudo apt install python3 python3-pip python3-venv postgresql postgresql-contrib

# Create database user
sudo -u postgres createuser --interactive psysuite_user
sudo -u postgres createdb psysuite_prod -O psysuite_user
```

#### **2. Application Deployment**
```bash
# Upload and deploy
scp -r web_app/ user@your-vps:/path/to/psysuite/
ssh user@your-vps
cd /path/to/psysuite/web_app

# Deploy
./deploy.sh traditional
python scripts/db/dev_add_testbis.py
```

#### **3. Production WSGI Server**
```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 run:app

# Or use systemd service
sudo systemctl enable psysuite-web
sudo systemctl start psysuite-web
```

#### **4. Reverse Proxy (Nginx)**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### **Docker Production Deployment**

#### **Complete Docker Setup**
```bash
# Deploy with Docker
./deploy.sh docker

# Check status
docker-compose ps
docker-compose logs web

# Scale if needed
docker-compose up --scale web=3
```

#### **Docker with SSL (Production)**
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  web:
    build: .
    environment:
      - FLASK_CONFIG=production
    volumes:
      - ./ssl:/ssl
  
  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/ssl
```

### **Monitoring & Maintenance**

#### **Health Checks**
```bash
# Basic health
curl http://your-server/api/health

# Detailed status  
curl http://your-server/api/status

# Upload service status
curl -H "X-API-Key: your-key" http://your-server/api/upload/status
```

#### **Log Monitoring**
```bash
# Application logs
tail -f logs/app.log

# Docker logs
docker-compose logs -f web

# System logs
journalctl -u psysuite-web -f
```

## Monitoring and Logging

### Health Checks

- `GET /api/health` - Basic health check for load balancers
- `GET /api/status` - Detailed system status for monitoring

### Logging

The system logs all user activities including:
- Login/logout events
- Test and user management actions
- Data access and downloads
- Experiment uploads
- System errors

Logs are stored in the `access_logs` table and can be viewed by administrators.

## 🔧 Troubleshooting

### **Common Issues & Solutions**

#### **1. Upload Failures (500 Errors)**
```bash
# ✅ FIXED: Automatic trial model creation
# The system now automatically creates missing trial models during uploads
# No manual intervention needed!

# Check logs for details
tail -f logs/app.log
```

#### **2. PyCharm Debug vs Run Mode Differences**  
```bash
# ✅ FIXED: Both modes now work identically
# The system handles debugger compatibility automatically
# Use either Run or Debug mode without issues
```

#### **3. Database Connection Issues**
```bash
# Check PostgreSQL status
systemctl status postgresql

# Verify database exists
sudo -u postgres psql -l | grep psysuite

# Reset database (development only)
bash scripts/dev-cleanup.sh
./deploy.sh traditional
```

#### **4. Docker Container Issues**
```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs web
docker-compose logs db

# Restart services
docker-compose restart

# Complete reset
bash scripts/docker-cleanup.sh
./deploy.sh docker
```

#### **5. Trial Table Missing**
```bash
# ✅ FIXED: Automatic table creation
# Tables are now created automatically when:
# - Tests are added via web interface
# - Tests are added via scripts  
# - Upload requests are received

# Manual verification (if needed)
python scripts/db/dev_add_testbis.py
```

### **Debug Tools**

#### **Development Debugging**
```bash
# Use the debug script with detailed logging
python scripts/run_debug.py

# Check database tables
python -c "
from app import create_app, db
app = create_app('development')
with app.app_context():
    inspector = db.inspect(db.engine)
    print('Tables:', inspector.get_table_names())
"
```

#### **Production Debugging**
```bash
# Check system status
./deploy.sh status

# View detailed logs
docker-compose logs --tail=100 web

# Database health check
curl http://localhost:5000/api/health
```

### **Environment Reset**

#### **Development Reset**
```bash
bash scripts/dev-cleanup.sh  # Removes venv, dev database
./deploy.sh traditional      # Fresh deployment
python scripts/db/dev_add_testbis.py  # Add test data
```

#### **Docker Reset**  
```bash
bash scripts/docker-cleanup.sh  # Removes containers, volumes, images
./deploy.sh docker              # Fresh deployment
./scripts/db/prod_add_testbis.sh  # Add test data
```

### **Performance Monitoring**

#### **Key Metrics**
- **Upload Success Rate**: Should be ~100% with automatic trial model creation
- **Response Times**: API endpoints should respond < 1s
- **Database Connections**: Monitor connection pool usage
- **Memory Usage**: Watch for memory leaks in long-running processes

#### **Monitoring Commands**
```bash
# API performance
curl -w "@curl-format.txt" http://localhost:5000/api/health

# Database performance  
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"

# System resources
htop
df -h
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is part of the PsySuite ecosystem. Please refer to the main PsySuite license for terms and conditions.

## Support

For support and questions:
- Check the troubleshooting section above
- Review the system logs for error details
- Contact the development team

## 📋 Management Scripts

### **Database Management**
```bash
# Development
bash scripts/dev-cleanup.sh           # Clean development environment
python scripts/db/dev_add_testbis.py  # Add TestBIS to development

# Production  
bash scripts/docker-cleanup.sh        # Clean Docker environment
./scripts/db/prod_add_testbis.sh      # Add TestBIS to production
```

### **Deployment Management**
```bash
./deploy.sh status        # Show current environment status
./deploy.sh traditional   # Deploy for development/VPS
./deploy.sh docker        # Deploy with Docker
./deploy.sh env-dev       # Switch to development config
./deploy.sh env-docker    # Switch to Docker config
./deploy.sh help          # Show all options
```

### **Development Tools**
```bash
python scripts/run_debug.py          # PyCharm-compatible debug server
python run.py                        # Standard Flask server
python init_db.py                    # Initialize database manually
```

## 🎯 Version History

### **v2.0.0** - Production-Ready Multi-Environment System ✨
- **🔧 Automatic Trial Table Management**: Tables created/updated automatically
- **🚀 Multi-Environment Deployment**: Development, Docker, and VPS support
- **🔄 Self-Healing Upload System**: On-demand trial model creation
- **🐛 PyCharm Debug Compatibility**: Fixed Run vs Debug mode issues
- **📦 Universal Deployment Script**: Single script handles all scenarios
- **🛡️ Process-Safe Operations**: Works across different server processes
- **🎯 Production VPS Deployment**: Successfully tested on Aruba VPS
- **📊 Enhanced Monitoring**: Comprehensive status and health checks

### **v1.0.0** - Initial Release
- User authentication and role management
- Test configuration and management  
- Experiment data upload and viewing
- Data export capabilities
- Android app integration