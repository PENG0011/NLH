# Accounting System - Setup & Deployment Guide

This guide covers local setup, deployment, and network access configuration for the Accounting (Ranking) system.

## Table of Contents
1. [Local Setup](#local-setup)
2. [Running the Service](#running-the-service)
3. [Network Access (WiFi)](#network-access-wifi)
4. [Deployment to Another Machine](#deployment-to-another-machine)
5. [System Information & Troubleshooting](#system-information--troubleshooting)

---

## Local Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Git (optional, for cloning the repository)

### Installation Steps

#### 1. Clone or Download the Project
```bash
# Option A: Clone from repository (if available)
git clone <repository-url>
cd ranking

# Option B: Download and extract manually
# Extract the project folder and navigate to it
cd ranking
```

#### 2. Create a Virtual Environment (Recommended)
```bash
# On macOS/Linux
python3 -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

If `requirements.txt` doesn't exist, install manually:
```bash
pip install fastapi uvicorn python-multipart
```

#### 4. Verify Installation
```bash
python -c "import fastapi; print('FastAPI version:', fastapi.__version__)"
```

---

## Running the Service

### Start the Server

#### Option 1: Development Mode (with auto-reload)
```bash
python main.py
```

The server will start at `http://localhost:8000`

#### Option 2: Production Mode (recommended for deployment)
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Verify the Server is Running
- Open your browser and visit: `http://localhost:8000`
- You should see the login/registration page

### Stop the Server
- Press `Ctrl+C` in the terminal

---

## Network Access (WiFi)

To allow other devices on the same WiFi network to access the service:

### Step 1: Find Your Local IP Address

#### On macOS/Linux:
```bash
# Method 1: Using ifconfig (macOS)
ifconfig | grep "inet " | grep -v 127.0.0.1

# Method 2: Using hostname (cross-platform)
hostname -I

# Method 3: Check in the app itself
# When the server is running, visit the admin panel for system info
curl http://localhost:8000/api/system_info
```

#### On Windows:
```cmd
ipconfig
```
Look for "IPv4 Address" under your network adapter (usually starts with 192.168.x.x or 10.x.x.x)

#### Example output:
```
192.168.1.100   (Your local IP)
```

### Step 2: Start Server Accessible on Network

The application already starts with `--host 0.0.0.0`, which makes it accessible from other devices.

```bash
python main.py
```

Or explicitly:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Step 3: Access from Another Device

On another device connected to the same WiFi:

1. Open a web browser
2. Visit: `http://<YOUR_LOCAL_IP>:8000`
   - Replace `<YOUR_LOCAL_IP>` with your actual IP (e.g., `http://192.168.1.100:8000`)

3. You should see the same login page

### Step 4: Get System Info from App

For convenience, you can get your system information directly from the app:

```bash
curl http://localhost:8000/api/system_info
```

Response example:
```json
{
  "local_ip": "192.168.1.100",
  "port": 8000,
  "access_url": "http://192.168.1.100:8000",
  "note": "Share this URL with other devices on the same WiFi network"
}
```

### Troubleshooting Network Access

**Problem: Other devices can't connect**

1. **Check firewall settings**
   - Ensure port 8000 is not blocked by your firewall
   - macOS: System Preferences → Security & Privacy → Firewall Options
   - Windows: Windows Defender Firewall → Allow an app through firewall

2. **Verify devices are on same WiFi**
   - Both devices must be connected to the same WiFi network
   - Check that they can ping each other

3. **Check IP address is correct**
   ```bash
   # From the other device, verify connectivity
   ping <YOUR_LOCAL_IP>
   ```

4. **Use correct port**
   - Default port is 8000
   - If you changed it, use the correct port in the URL

---

## Deployment to Another Machine

### Option 1: Using Python (Recommended for Easy Setup)

#### On the Target Machine:

1. **Copy project files**
   ```bash
   # Copy the entire ranking folder to the target machine
   scp -r /path/to/ranking user@target-machine:/home/user/
   
   # Or use USB drive / cloud storage if SSH is unavailable
   ```

2. **Set up on target machine**
   ```bash
   cd ranking
   
   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Start the server
   python main.py
   ```

3. **Verify**
   - Visit `http://localhost:8000` on the target machine
   - Or from another device: `http://<target-ip>:8000`

### Option 2: Using Docker (For Containerized Deployment)

#### Create a Dockerfile in the project root:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Copy project files
COPY . /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "main.py"]
```

#### Build and run:

```bash
# Build the image
docker build -t accounting-system:latest .

# Run the container
docker run -d \
  --name accounting \
  -p 8000:8000 \
  -v accounting-data:/app/data \
  accounting-system:latest

# Stop the container
docker stop accounting

# View logs
docker logs accounting
```

### Option 3: Using a Process Manager (PM2 for Node-like experience)

For persistent deployment on a server:

```bash
# Install PM2 globally (requires Node.js)
npm install -g pm2

# Create ecosystem.config.js
cat > ecosystem.config.js << 'EOF'
module.exports = {
  apps: [{
    name: 'accounting-system',
    script: './main.py',
    interpreter: 'python3',
    instances: 1,
    exec_mode: 'fork',
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'production'
    }
  }]
};
EOF

# Start with PM2
pm2 start ecosystem.config.js

# Monitor
pm2 monit

# View logs
pm2 logs accounting-system
```

### Option 4: Cloud Deployment (AWS, Google Cloud, Heroku, etc.)

#### For Heroku:

1. **Create Procfile** in project root:
   ```
   web: uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

2. **Deploy:**
   ```bash
   heroku create accounting-system
   git push heroku main
   heroku open
   ```

#### For AWS EC2:

1. Launch an EC2 instance (Ubuntu 20.04 LTS)
2. SSH into the instance
3. Follow "Option 1: Using Python" steps above
4. Configure security groups to allow port 8000
5. Optionally, use Nginx as reverse proxy

---

## System Information & Troubleshooting

### Check System Information

While the server is running:

```bash
curl http://localhost:8000/api/system_info
```

This returns:
- Local IP address
- Port
- Full access URL
- Network access instructions

### Database & Data Files

The application stores data in:
- `score_system.db` - SQLite database (all scores, users, sessions)
- `data/users.json` - User list (for backup)
- `data/seats/` - Seat arrangement history
- `data/sessions/` - Game session history

**Backup Important Data:**
```bash
# Backup database before major operations
cp score_system.db score_system.db.backup

# Backup all data
tar -czf ranking-backup-$(date +%Y%m%d).tar.gz score_system.db data/
```

### Admin Operations

#### Reset All Data (from API)

**Warning: This deletes everything!**

```bash
curl -X POST http://localhost:8000/api/reset_all \
  -H "Content-Type: application/json" \
  -d '{"admin_user": "peng"}'
```

Or use the UI:
1. Login as admin (peng)
2. Go to Points tab → Admin Control
3. Click "⚠️ 清空所有数据" (Clear All Data)

#### View All Users

```bash
curl http://localhost:8000/api/users_all
```

#### Get Scores & Leaderboard

```bash
curl http://localhost:8000/api/scores
```

### Performance Optimization

For large number of concurrent users:

1. **Use production server:**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4 --worker-class uvicorn.workers.UvicornWorker
   ```

2. **Add Nginx reverse proxy** (Linux/macOS):
   ```nginx
   server {
       listen 80;
       server_name _;
       
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

3. **Database optimization:**
   - Regular backups: `cp score_system.db score_system.db.backup`
   - Consider upgrading to PostgreSQL for large deployments

### Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Port 8000 already in use | `lsof -i :8000` (macOS/Linux) or `netstat -ano \| findstr :8000` (Windows), then kill the process or use different port: `uvicorn main:app --port 8001` |
| "Module not found" error | Activate virtual environment and reinstall: `pip install -r requirements.txt` |
| Can't connect from other devices | Check firewall, verify IP address, ensure same WiFi network |
| Database locked error | Close all connections to the database, restart the server |
| WebSocket connection fails | Check that WebSocket is properly supported (usually automatic) |
| Slow performance | Run with workers: `--workers 4` and monitor CPU/memory usage |

### Support & Debugging

**Enable debug logging:**

Edit `main.py`:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Check server logs:**
```bash
# From application output
# All requests and errors are logged to console
```

---

## Quick Start Summary

### For Local Development:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
# Visit http://localhost:8000
```

### For Network Access:
```bash
# Get your IP
curl http://localhost:8000/api/system_info

# Share the access_url with others on the same WiFi
```

### For Another Machine:
```bash
# Copy files, install dependencies, and run same as local setup
```

---

## Features & Default Users

- **Default Admin**: Username `peng`
- **Users support**: Chinese characters in usernames ✅
- **Avatars**: 50+ unique emoji avatars (exclusive per user)
- **Admin functions**: 
  - Create new game sessions
  - Manage users (activate/deactivate)
  - Rebalance scores
  - Clear all data

---

## License & Support

For issues or questions, check the main README.md or contact the development team.

Happy accounting! 🎉
