# PsySuite Web Manager - Deployment Summary

## Quick Answer to Your Questions

### 1. Do I need to install a web server on Ubuntu?

**For Docker deployment (RECOMMENDED):** No, everything is included in containers.
**For traditional deployment:** Yes, you'll need Nginx + Python + PostgreSQL.

### 2. Can I put everything in a Docker container?

**YES!** This is the recommended approach. Your project already includes complete Docker configuration.

### 3. Deploying to Aruba hosting

**Aruba Cloud/VPS:** Use Docker deployment
**Aruba Shared Hosting:** Use traditional Python deployment with SQLite

---

## 🚀 Fastest Deployment Method (Docker)

### Prerequisites
- Ubuntu server (Aruba Cloud/VPS)
- Docker and Docker Compose installed

### One-Command Deployment

```bash
cd psysuite_web
./deploy.sh docker
```

This will:
1. ✅ Build all containers (web app, database, nginx)
2. ✅ Start all services
3. ✅ Initialize the database
4. ✅ Set up reverse proxy with Nginx
5. ✅ Create the default admin user
6. ✅ Run health checks

**Result:** Your app will be running at `http://your-server-ip`

---

## 📋 Step-by-Step Instructions

### Option A: Aruba Cloud/VPS with Docker (Recommended)

1. **Order Aruba Cloud VPS** with Ubuntu 20.04+

2. **Connect to your server:**
   ```bash
   ssh root@your-server-ip
   ```

3. **Install Docker:**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   sudo apt install docker-compose
   ```

4. **Upload your project:**
   ```bash
   # From your local machine
   scp -r psysuite_web/ root@your-server-ip:/root/
   ```

5. **Deploy:**
   ```bash
   # On the server
   cd psysuite_web
   ./deploy.sh docker
   ```

6. **Configure domain** (in Aruba control panel):
   - Point your domain to server IP
   - Wait for DNS propagation

7. **Setup SSL** (optional but recommended):
   ```bash
   sudo apt install certbot
   sudo certbot certonly --standalone -d your-domain.com
   ```

### Option B: Aruba Shared Hosting

1. **Prepare files for shared hosting:**
   ```bash
   cd psysuite_web
   ./deploy.sh aruba
   ```

2. **Upload to Aruba:**
   - Use the generated `upload_to_aruba.sh` script
   - Or manually upload via FTP/cPanel

3. **Initialize on server:**
   ```bash
   # On Aruba server (via SSH or cPanel terminal)
   python3 init_db.py
   ```

---

## 🔧 Configuration Files

### Environment Variables (.env)

```bash
# Copy and edit the example
cp .env.example .env
nano .env
```

Key settings to change:
- `SECRET_KEY`: Generate a secure random string
- `DATABASE_URL`: Your database connection
- `MAIL_*`: Email settings for notifications

### Docker Configuration

Your project includes:
- `Dockerfile`: Python app container
- `docker-compose.yml`: Multi-service setup
- `nginx.conf`: Reverse proxy configuration

---

## 🌐 Accessing Your Application

### Default Admin Account
- **Email:** alberto.inuggi@gmail.com
- **Password:** antares
- **⚠️ Change this immediately in production!**

### URLs
- **Main App:** `http://your-domain.com`
- **API Health:** `http://your-domain.com/api/health`
- **Admin Panel:** `http://your-domain.com/admin`

---

## 📱 Android App Configuration

Update your Android app to point to the web backend:

```kotlin
// In ResultsManager or configuration
private val webApiUrl = "https://your-domain.com"
```

---

## 🔍 Monitoring and Maintenance

### Health Checks
```bash
# Check if app is running
curl http://your-domain.com/api/health

# Detailed system status
curl http://your-domain.com/api/status
```

### View Logs
```bash
# Docker deployment
docker-compose logs -f web

# Traditional deployment
tail -f logs/app.log
```

### Backup Database
```bash
# Docker deployment
docker-compose exec db pg_dump -U psysuite psysuite_web > backup.sql

# Traditional deployment
pg_dump -U psysuite psysuite_web > backup.sql
```

---

## 🆘 Troubleshooting

### Common Issues

**"Port already in use"**
```bash
sudo lsof -i :5000
sudo kill -9 <PID>
```

**"Database connection failed"**
```bash
# Check if PostgreSQL is running
docker-compose ps
# or
sudo systemctl status postgresql
```

**"Permission denied"**
```bash
sudo chown -R $USER:$USER /path/to/psysuite_web
```

### Getting Help

1. **Check logs first:** `docker-compose logs web`
2. **Test health endpoint:** `curl http://localhost:5000/api/health`
3. **Verify configuration:** Check `.env` file
4. **Database issues:** Check database connectivity

---

## 💡 Recommendations

### For Production

1. **Use Docker deployment** - most reliable and portable
2. **Setup SSL certificate** - essential for security
3. **Configure backups** - automate database backups
4. **Monitor logs** - set up log rotation and monitoring
5. **Change default passwords** - immediately after deployment

### For Development/Testing

1. **Use traditional deployment** - easier to debug
2. **Use SQLite database** - simpler setup
3. **Enable debug mode** - set `FLASK_CONFIG=development`

---

## 📞 Aruba-Specific Notes

### Aruba Cloud (VPS)
- ✅ Full Docker support
- ✅ Root access
- ✅ Custom domains
- ✅ SSL certificates
- **Recommended approach:** Docker deployment

### Aruba Shared Hosting
- ❌ No Docker support
- ❌ Limited Python packages
- ✅ Basic Python support
- ✅ SQLite database
- **Recommended approach:** Traditional deployment with SQLite

### Domain Configuration
In your Aruba control panel:
- **A Record:** `@` → `YOUR_SERVER_IP`
- **A Record:** `www` → `YOUR_SERVER_IP`

---

## 🎯 Quick Start Checklist

- [ ] Choose deployment method (Docker recommended)
- [ ] Prepare server (Aruba Cloud/VPS or shared hosting)
- [ ] Upload project files
- [ ] Configure environment variables
- [ ] Run deployment script
- [ ] Test application access
- [ ] Configure domain name
- [ ] Setup SSL certificate
- [ ] Change default admin password
- [ ] Configure Android app to use web backend

**Total deployment time:** 15-30 minutes with Docker, 1-2 hours traditional

Your PsySuite Web Manager is production-ready and includes all necessary components for a complete deployment! 🚀