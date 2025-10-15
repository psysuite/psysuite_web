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
    
    # Check if .env file exists
    if [ ! -f .env ]; then
        print_warning ".env file not found. Creating from example..."
        if [ -f .env.example ]; then
            cp .env.example .env
            print_warning "Please edit .env file with your production settings before continuing."
            read -p "Press Enter to continue after editing .env file..."
        else
            print_error ".env.example file not found. Please create .env file manually."
            exit 1
        fi
    fi
    
    # Build and start services
    print_status "Building and starting Docker services..."
    docker-compose down 2>/dev/null || true
    docker-compose up --build -d
    
    # Wait for services to start
    print_status "Waiting for services to start..."
    sleep 10
    
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
    else
        print_error "❌ Application health check failed"
        print_status "Checking logs..."
        docker-compose logs web
        exit 1
    fi
}

# Function to deploy traditionally
deploy_traditional() {
    print_status "Starting traditional deployment..."
    
    # Check Python version
    if ! command_exists python3; then
        print_error "Python 3 is not installed. Please install Python 3.7+ first."
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if [[ $(echo "$PYTHON_VERSION < 3.7" | bc -l) -eq 1 ]]; then
        print_error "Python 3.7+ is required. Current version: $PYTHON_VERSION"
        exit 1
    fi
    
    # Create virtual environment
    print_status "Creating Python virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    
    # Install dependencies
    print_status "Installing Python dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Setup environment variables
    if [ ! -f .env ]; then
        print_warning ".env file not found. Creating from example..."
        if [ -f .env.example ]; then
            cp .env.example .env
            # Use SQLite for traditional deployment
            sed -i 's|DATABASE_URL=.*|DATABASE_URL=sqlite:///psysuite.db|' .env
            print_warning "Using SQLite database for traditional deployment."
            print_warning "Please edit .env file if you want to use PostgreSQL."
        fi
    fi
    
    # Initialize database
    print_status "Initializing database..."
    python init_db.py
    
    # Start application
    print_status "Starting application..."
    print_status "🌐 Application will be available at: http://localhost:5000"
    print_status "📊 Admin login: alberto.inuggi@gmail.com / antares"
    print_status "Press Ctrl+C to stop the application"
    
    python run.py
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
tar -czf psysuite_web.tar.gz \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='*.pyc' \
    --exclude='tests' \
    --exclude='docker-compose.yml' \
    --exclude='Dockerfile' \
    --exclude='nginx.conf' \
    .

echo "Archive created: psysuite_web.tar.gz"
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
    print_status "3. Extract psysuite_web.tar.gz on your Aruba server"
    print_status "4. Run: python3 init_db.py on the server"
}

# Function to show help
show_help() {
    echo "PsySuite Web Manager Deployment Script"
    echo ""
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  docker      Deploy using Docker (recommended)"
    echo "  traditional Deploy using traditional Python setup"
    echo "  aruba       Setup files for Aruba hosting"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 docker      # Deploy with Docker"
    echo "  $0 traditional # Deploy with Python virtual environment"
    echo "  $0 aruba       # Prepare files for Aruba hosting"
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
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown option: $1"
        show_help
        exit 1
        ;;
esac