#!/bin/bash
# SSL Setup Script for PsySuite Web Manager

echo "🔒 Setting up SSL for PsySuite Web Manager"
echo "=========================================="

# Check if domain is provided
if [ -z "$1" ]; then
    echo "❌ Error: Please provide your domain name"
    echo "Usage: ./setup-ssl.sh your-domain.com"
    exit 1
fi

DOMAIN=$1
echo "🌐 Domain: $DOMAIN"

# Create SSL directory
mkdir -p ssl

# Option 1: Let's Encrypt (Recommended for production)
echo ""
echo "🔐 SSL Certificate Options:"
echo "1. Let's Encrypt (Free, Automatic)"
echo "2. Self-signed (Development only)"
echo "3. Custom certificate (I have my own)"
echo ""
read -p "Choose option (1-3): " choice

case $choice in
    1)
        echo "📋 Let's Encrypt Setup Instructions:"
        echo "1. Install certbot:"
        echo "   sudo apt install certbot"
        echo ""
        echo "2. Stop nginx temporarily:"
        echo "   docker-compose stop nginx"
        echo ""
        echo "3. Get certificate:"
        echo "   sudo certbot certonly --standalone -d $DOMAIN"
        echo ""
        echo "4. Copy certificates:"
        echo "   sudo cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem ssl/"
        echo "   sudo cp /etc/letsencrypt/live/$DOMAIN/privkey.pem ssl/"
        echo ""
        echo "5. Update nginx config and restart:"
        echo "   # Edit nginx.conf to enable SSL"
        echo "   docker-compose up -d nginx"
        ;;
    2)
        echo "🔧 Creating self-signed certificate..."
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout ssl/privkey.pem \
            -out ssl/fullchain.pem \
            -subj "/C=IT/ST=State/L=City/O=Organization/CN=$DOMAIN"
        echo "✅ Self-signed certificate created in ssl/"
        ;;
    3)
        echo "📁 Place your certificate files in ssl/ directory:"
        echo "   ssl/fullchain.pem (certificate)"
        echo "   ssl/privkey.pem (private key)"
        ;;
esac

echo ""
echo "🔧 Next steps:"
echo "1. Update nginx.conf to enable SSL"
echo "2. Restart nginx: docker-compose restart nginx"
echo "3. Test: https://$DOMAIN"