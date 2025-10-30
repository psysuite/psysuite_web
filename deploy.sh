#!/bin/bash

# PsySuite Web Manager Deployment Script
# This script helps deploy the application in different environments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to setup Docker environment
setup_docker_environment() {
    print_status "Setting up Docker environment configuration..."
    
    # Check if .env.docker exists
    if [ ! -f .env.docker ]; then
        print_error ".env.docker file not found. This file is required for Docker deployment."
        print_status "Please create .env.docker with your Docker/production settings."
        exit 1
    fi
    
    # Copy .env.docker to .env
    print_status "Switching to Docker configuration..."
    cp .env.docker .env
    
    # Verify .env file exists and has content
    if [ ! -f .env ] || [ ! -s .env ]; then
        print_error "Failed to create .env file from .env.docker"
        exit 1
    fi
    
    print_status "✅ Docker environment configured successfully"
    print_status "📋 Current settings:"
    print_status "   - Database: PostgreSQL in Docker (db:5432)"
    print_status "   - Environment: production"
    print_status "   - Port: 5000 (via Docker)"
}

# Function to setup PyCharm/development environment
setup_development_environment() {
    print_status "Setting up development environment configuration..."
    
    # Check if .env.development exists
    if [ ! -f .env.development ]; then
        print_error ".env.development file not found. This file is required for development deployment."
        print_status "Please create .env.development with your development settings."
        exit 1
    fi
    
    # Copy .env.development to .env
    print_status "Switching to PyCharm development configuration..."
    cp .env.development .env
    
    # Verify .env file exists and has content
    if [ ! -f .env ] || [ ! -s .env ]; then
        print_error "Failed to create .env file from .env.development"
        exit 1
    fi
    
    print_status "✅ Development environment configured successfully"
    print_status "📋 Current settings:"
    print_status "   - Database: PostgreSQL on localhost:5432"
    print_status "   - Environment: development"
    print_status "   - Port: 5001 (via scripts/debug.py)"
}

# Function to deploy with Docker
deploy_docker() {
    print_status "Starting Docker deployment..."
    
    # Check if Docker is installed
    if ! command_exists docker; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command_exists docker-compose; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Handle environment configuration
    setup_docker_environment
    
    # Stop any existing services and clean up
    print_status "Stopping existing services..."
    docker-compose down 2>/dev/null || true
    
    # Stop any other Docker containers that might be using port 5000
    print_status "Checking for Docker containers using port 5000..."
    CONTAINERS_ON_5000=$(docker ps --format "table {{.Names}}\t{{.Ports}}" | grep ":5000->" | awk '{print $1}' || true)
    if [ ! -z "$CONTAINERS_ON_5000" ]; then
        print_warning "Found containers using port 5000: $CONTAINERS_ON_5000"
        print_status "Stopping conflicting containers..."
        echo "$CONTAINERS_ON_5000" | xargs -r docker stop
        sleep 2
    fi
    
    # Kill any process using port 5000
    print_status "Checking for other processes using port 5000..."
    if command_exists lsof && lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "Port 5000 is still in use. Attempting to free it..."
        sudo pkill -f "python.*run.py" 2>/dev/null || true
        sudo pkill -f "flask run" 2>/dev/null || true
        sleep 2
    fi
    
    # Build and start services
    print_status "Building and starting Docker services..."
    docker-compose up --build -d
    
    # Wait for services to start
    print_status "Waiting for services to start..."
    sleep 10
    
    # Wait for database to be ready
    print_status "Waiting for database to be ready..."
    for i in {1..30}; do
        if docker-compose exec -T db pg_isready -U psysuite -d psysuite_web >/dev/null 2>&1; then
            print_status "Database is ready!"
            break
        fi
        echo "Waiting for database... ($i/30)"
        sleep 2
    done
    
    # Initialize database
    print_status "Initializing database..."
    docker-compose exec -T web python init_db.py
    
    # Check health
    print_status "Checking application health..."
    sleep 5
    
    if curl -f http://localhost:5000/api/health >/dev/null 2>&1; then
        print_status "✅ Application is running successfully!"
        print_status "🌐 Access your application at: http://localhost"
        print_status "📊 Admin login: alberto.inuggi@gmail.com / antares"
        print_status ""
        print_status "💡 Additional database management:"
        print_status "   - Run './prod-db-setup.sh' to reinitialize database"
        print_status "   - Run 'docker-compose exec web python -c \"...\"' to add TestBIS"
    else
        print_error "❌ Application health check failed"
        print_status "Checking logs..."
        docker-compose logs web
        exit 1
    fi
}

# Function to setup local PostgreSQL database
setup_local_database() {
    print_status "Setting up local PostgreSQL database..."
    
    # Database configuration from .env.development
    DB_USER="psysuite_user"
    DB_PASSWORD="psysuite123"
    DB_NAME="psysuite_dev"
    
    print_status "📋 Database configuration:"
    print_status "   User: $DB_USER"
    print_status "   Database: $DB_NAME"
    print_status "   Host: localhost:5432"
    
    # Check if PostgreSQL is running
    if ! pgrep -x "postgres" > /dev/null; then
        print_error "PostgreSQL is not running. Please start it first:"
        print_error "   sudo systemctl start postgresql"
        exit 1
    fi
    
    print_status "✅ PostgreSQL is running"
    
    # Create user and database
    print_status "🔨 Creating database user and database..."
    
    sudo -u postgres psql << EOF
-- Create user if it doesn't exist
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '$DB_USER') THEN
        CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
        RAISE NOTICE 'User $DB_USER created';
    ELSE
        ALTER USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
        RAISE NOTICE 'User $DB_USER password updated';
    END IF;
END
\$\$;

-- Create database if it doesn't exist
SELECT 'CREATE DATABASE $DB_NAME OWNER $DB_USER'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
ALTER USER $DB_USER CREATEDB;

\q
EOF
    
    print_status "✅ Database setup completed successfully!"
}

# Function to deploy traditionally
deploy_traditional() {
    print_status "Starting traditional deployment..."
    
    # Check Python version
    if ! command_exists python3; then
        print_error "Python 3 is not installed. Please install Python 3.7+ first."
        exit 1
    fi
    
    # Check Python version using Python itself
    python3 -c "
import sys
if sys.version_info < (3, 7):
    print('ERROR: Python 3.7+ is required. Current version: {}.{}'.format(sys.version_info.major, sys.version_info.minor))
    exit(1)
else:
    print('Python version {}.{} is compatible'.format(sys.version_info.major, sys.version_info.minor))
"
    if [ $? -ne 0 ]; then
        exit 1
    fi
    
    # Setup local PostgreSQL database first
    setup_local_database
    
    # Check for existing virtual environment
    if [ -d ../venv ] && [ -x ../venv/bin/python ]; then
        print_status "Using existing virtual environment in parent directory..."
        source ../venv/bin/activate
    elif [ -d venv ] && [ -x venv/bin/python ]; then
        print_status "Using existing virtual environment in current directory..."
        source venv/bin/activate
    else
        print_status "Creating fresh Python virtual environment..."
        # Remove broken venv if it exists
        [ -d venv ] && rm -rf venv
        python3 -m venv venv
        source venv/bin/activate
    fi
    
    # Install dependencies
    print_status "Installing Python dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Setup environment variables
    setup_development_environment
    
    # Initialize database
    print_status "Initializing database..."
    python init_db.py
    
    # Start application
    print_status "Starting application..."
    print_status "🌐 Application will be available at: http://localhost:5001"
    print_status "📊 Admin login: alberto.inuggi@gmail.com / antares"
    print_status "Press Ctrl+C to stop the application"
    
    python run.py
#    python scripts/debug_run.py
}

# Function to setup for Aruba hosting
setup_aruba() {
    print_status "Setting up for Aruba hosting..."
    
    # Create Aruba-specific configuration
    cat > .env.aruba << 'EOF'
FLASK_CONFIG=production
DATABASE_URL=sqlite:///psysuite.db
SECRET_KEY=change-this-to-a-secure-random-string
MAIL_SERVER=smtps.aruba.it
MAIL_PORT=465
MAIL_USE_SSL=true
MAIL_USERNAME=your-email@yourdomain.com
MAIL_PASSWORD=your-email-password
EOF
    
    # Create requirements for shared hosting
    cat > requirements_aruba.txt << 'EOF'
Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-Login==0.6.3
Flask-WTF==1.1.1
Flask-Migrate==4.0.5
Flask-Mail==0.9.1
Werkzeug==2.3.7
WTForms==3.0.1
SQLAlchemy==2.0.21
python-dotenv==1.0.0
email-validator==2.0.0
bcrypt==4.0.1
requests==2.31.0
EOF
    
    # Create upload script
    cat > upload_to_aruba.sh << 'EOF'
#!/bin/bash
# Upload script for Aruba hosting
# Usage: ./upload_to_aruba.sh your-ftp-host your-username

if [ $# -ne 2 ]; then
    echo "Usage: $0 <ftp-host> <username>"
    echo "Example: $0 ftp.your-domain.com your-username"
    exit 1
fi

FTP_HOST=$1
FTP_USER=$2

echo "Uploading to Aruba hosting..."
echo "Host: $FTP_HOST"
echo "User: $FTP_USER"

# Create archive excluding unnecessary files
tar -czf web_app.tar.gz \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='*.pyc' \
    --exclude='tests' \
    --exclude='docker-compose.yml' \
    --exclude='Dockerfile' \
    --exclude='nginx.conf' \
    .

echo "Archive created: web_app.tar.gz"
echo "Please upload this file to your Aruba hosting and extract it."
echo "Then run: python3 init_db.py to initialize the database."
EOF
    
    chmod +x upload_to_aruba.sh
    
    print_status "✅ Aruba hosting setup complete!"
    print_status "📁 Created files:"
    print_status "   - .env.aruba (configuration for Aruba)"
    print_status "   - requirements_aruba.txt (minimal requirements)"
    print_status "   - upload_to_aruba.sh (upload helper script)"
    print_status ""
    print_status "📋 Next steps for Aruba hosting:"
    print_status "1. Edit .env.aruba with your settings"
    print_status "2. Run: ./upload_to_aruba.sh your-ftp-host your-username"
    print_status "3. Extract web_app.tar.gz on your Aruba server"
    print_status "4. Run: python3 init_db.py on the server"
}

# Function to show deployment status
show_status() {
    print_status "PsySuite Web Manager - Deployment Status"
    echo ""
    
    # Check current environment
    if [ -f .env ]; then
        print_status "📄 Active environment file: .env"
        if grep -q "FLASK_CONFIG=production" .env 2>/dev/null; then
            echo "   🐳 Environment: Docker/Production"
        elif grep -q "FLASK_CONFIG=development" .env 2>/dev/null; then
            echo "   🐍 Environment: PyCharm/Development"
        else
            echo "   ❓ Environment: Unknown"
        fi
        
        # Show database URL (masked)
        if grep -q "DATABASE_URL" .env; then
            DB_URL=$(grep "DATABASE_URL" .env | cut -d'=' -f2- | sed 's/:[^@]*@/:***@/')
            echo "   🗄️  Database: $DB_URL"
        fi
    else
        print_warning "No active .env file found"
    fi
    
    echo ""
    
    # Check available environment files
    print_status "📁 Available environment files:"
    [ -f .env.docker ] && echo "   ✅ .env.docker (Docker/Production)" || echo "   ❌ .env.docker (missing)"
    [ -f .env.development ] && echo "   ✅ .env.development (PyCharm/Development)" || echo "   ❌ .env.development (missing)"
    [ -f .env.example ] && echo "   ✅ .env.example (template)" || echo "   ❌ .env.example (missing)"
    
    echo ""
    
    # Check Docker status
    if command_exists docker && command_exists docker-compose; then
        print_status "🐳 Docker status:"
        if docker-compose ps 2>/dev/null | grep -q "Up"; then
            echo "   ✅ Docker containers running:"
            docker-compose ps 2>/dev/null | grep -v "^Name" | head -10
        else
            echo "   ❌ No Docker containers running"
        fi
    else
        print_warning "Docker or docker-compose not available"
    fi
    
    echo ""
    
    # Check Python virtual environment
    if [ -d ../venv ]; then
        print_status "🐍 Python virtual environment: ✅ Available (in parent directory)"
    elif [ -d venv ]; then
        print_status "🐍 Python virtual environment: ✅ Available (in current directory)"
    else
        print_status "🐍 Python virtual environment: ❌ Not found"
    fi
    
    echo ""
    
    # Show available management scripts
    print_status "🔧 Available management scripts:"
    [ -f scripts/run_debug.py ] && echo "   ✅ scripts/run_debug.py (development server)" || echo "   ❌ scripts/run_debug.py"
    [ -f scripts/docker-cleanup.sh ] && echo "   ✅ scripts/docker-cleanup.sh (Docker cleanup)" || echo "   ❌ scripts/docker-cleanup.sh"
    [ -f scripts/dev-cleanup.sh ] && echo "   ✅ scripts/dev-cleanup.sh (development cleanup)" || echo "   ❌ scripts/dev-cleanup.sh"
    [ -f scripts/db/dev_add_testbis.py ] && echo "   ✅ scripts/db/dev_add_testbis.py (add TestBIS to dev)" || echo "   ❌ scripts/db/dev_add_testbis.py"
    [ -f scripts/db/prod_add_testbis.sh ] && echo "   ✅ scripts/db/prod_add_testbis.sh (add TestBIS to prod)" || echo "   ❌ scripts/db/prod_add_testbis.sh"
}

# Function to show help
show_help() {
    echo "PsySuite Web Manager Deployment Script"
    echo ""
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  docker      Deploy using Docker (production)"
    echo "  traditional Deploy using traditional Python setup (development)"
    echo "  aruba       Setup files for Aruba hosting"
    echo "  env-docker  Switch to Docker environment (.env.docker → .env)"
    echo "  env-dev     Switch to development environment (.env.development → .env)"
    echo "  status      Show current environment and container status"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 docker      # Deploy with Docker using .env.docker"
    echo "  $0 traditional # Deploy with Python venv using .env.development"
    echo "  $0 env-docker  # Just switch to Docker environment"
    echo "  $0 env-dev     # Just switch to development environment"
    echo "  $0 status      # Show current deployment status"
    echo ""

    echo "Database Management:"
    echo "  ./prod-db-setup.sh            # Reinitialize production database (Docker)"
    echo "  scripts/db/add_testbis.py     # Add TestBIS test to database"
    echo ""
    echo "Cleanup Scripts:"
    echo "  ./scripts/docker-cleanup.sh   # Complete Docker cleanup (removes everything)"
    echo "  ./scripts/dev-cleanup.sh      # Development environment cleanup (venv + dev DB)"
    echo ""
    echo "Environment Files:"
    echo "  .env.docker      # Docker/production configuration"
    echo "  .env.development # PyCharm/development configuration"
    echo "  .env             # Active configuration (auto-generated by deploy.sh)"
}

# Main script logic
case "${1:-help}" in
    docker)
        deploy_docker
        ;;
    traditional)
        deploy_traditional
        ;;
    aruba)
        setup_aruba
        ;;
    env-docker)
        setup_docker_environment
        ;;
    env-dev)
        setup_development_environment
        ;;
    status)
        show_status
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown option: $1"
        show_help
        exit 1
        ;;
esac