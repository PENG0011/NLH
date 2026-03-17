# Accounting System - Documentation Index

Welcome! Here's a complete guide to all the documentation and features of the Accounting System.

---

## 📚 Documentation Files

### Quick Start (Choose Your Path)

#### 👤 I just want to play right now
→ **Read:** [QUICK_REFERENCE.md](QUICK_REFERENCE.md) (2 min read)
- Start server: `python main.py`
- Visit: `http://localhost:8000`
- Register and play!

#### 🎮 I want to play on multiple devices (WiFi)
→ **Read:** [WIFI_SETUP.md](WIFI_SETUP.md) (5 min read)
- Get your IP address
- Share URL with other devices
- All devices on same WiFi access the system

#### 🏗️ I want to set up everything from scratch
→ **Read:** [SETUP_GUIDE.md](SETUP_GUIDE.md) (15 min read)
- Complete installation guide
- Local setup instructions
- Production deployment options
- Troubleshooting guide

#### 📋 I want to know what changed in this version
→ **Read:** [CHANGES_SUMMARY.md](CHANGES_SUMMARY.md) (5 min read)
- What's new in version 2.0
- Feature implementation details
- API reference

---

## 🎯 What You Can Do Now

### For Players

✅ **Play locally**
- Start: `python main.py`
- Access: `http://localhost:8000`

✅ **Play on network**
- Get IP: `curl http://localhost:8000/api/system_info`
- Share: `http://your-ip:8000`
- Others join from any device on same WiFi

✅ **Use Chinese usernames**
- Register: 小明, 张三, 中文用户, etc.
- Full Unicode support

✅ **Track scores**
- Buy in/cash out
- Win/loss tracking
- Real-time leaderboard
- Trend charts

✅ **Seat assignment**
- Random seating
- Table view with avatars
- Mirror view option

### For Admins

✅ **Manage sessions**
- Create new game sessions
- Archive old sessions
- Reset scores

✅ **Manage users**
- Activate/deactivate players
- Manage avatars
- View all user info

✅ **Reset data**
- Clear all users and scores
- Complete system reset
- Two-step confirmation for safety

✅ **Monitor system**
- Check system info: `/api/system_info`
- View activity logs
- Monitor connected users

---

## 🚀 Quick Start Paths

### Path 1: Play Locally (5 minutes)

```bash
# 1. Start server
cd ranking
python main.py

# 2. Open browser
# http://localhost:8000

# 3. Register and play!
```

### Path 2: Play on Network (10 minutes)

```bash
# 1. Start server
python main.py

# 2. Get IP address
curl http://localhost:8000/api/system_info
# Look for "access_url": "http://192.168.1.100:8000"

# 3. Share with other devices
# Open http://192.168.1.100:8000 on any device
# Make sure they're on same WiFi!
```

### Path 3: Deploy to Another Machine (20 minutes)

```bash
# 1. Copy project
scp -r ranking user@host:/path/to/

# 2. Install on target
ssh user@host
cd ranking
pip install fastapi uvicorn python-multipart

# 3. Start server
python main.py

# 4. Access from anywhere on network
# http://target-ip:8000
```

---

## 📖 Feature Documentation

### Features Added in Version 2.0

#### 1. Chinese Character Support for Usernames ✅
- **Status:** Fully supported
- **Examples:** 小明, 张三, 中文用户, abc中文123
- **Documentation:** See [SETUP_GUIDE.md](SETUP_GUIDE.md#features--default-users)
- **No action needed:** Already works!

#### 2. Reset Button for Admin ✅
- **Location:** Points tab → Admin Control panel
- **Button:** "⚠️ 清空所有数据" (red button)
- **What it does:** Deletes all users, scores, sessions, and data
- **Safety:** Requires two confirmation dialogs
- **Documentation:** See [QUICK_REFERENCE.md](QUICK_REFERENCE.md#admin-operations)

#### 3. Setup Guides for Deployment ✅
- **SETUP_GUIDE.md:** Full setup and deployment manual
- **QUICK_REFERENCE.md:** One-page quick reference
- **WIFI_SETUP.md:** Network access setup
- **This file:** Documentation index

#### 4. WiFi Network Access ✅
- **How:** `curl http://localhost:8000/api/system_info`
- **Returns:** IP address and access URL
- **Share with:** Any device on same WiFi
- **Documentation:** See [WIFI_SETUP.md](WIFI_SETUP.md)

---

## 🔧 Common Tasks

### Getting Your IP Address

```bash
# Using the app (easiest)
curl http://localhost:8000/api/system_info

# Manual methods
# macOS
ifconfig | grep "inet " | grep -v 127

# Linux  
hostname -I

# Windows
ipconfig
```

### Starting the Server

```bash
# Development mode (auto-reload)
python main.py

# Production mode (4 workers)
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Resetting All Data

```bash
# Via API
curl -X POST http://localhost:8000/api/reset_all \
  -H "Content-Type: application/json" \
  -d '{"admin_user": "peng"}'

# Via UI
# 1. Login as admin
# 2. Points tab → Admin Control
# 3. Click "⚠️ 清空所有数据"
# 4. Confirm twice
```

### Backing Up Data

```bash
# Backup database
cp score_system.db score_system.db.backup-$(date +%Y%m%d)

# Backup everything
tar -czf ranking-backup-$(date +%Y%m%d).tar.gz score_system.db data/
```

---

## 📱 Using on Mobile Devices

The system is fully responsive and works great on mobile!

### On iPhone/iPad:
1. Connect to same WiFi as server
2. Open Safari
3. Go to: `http://your-server-ip:8000`
4. Login/register
5. Full app experience!

### On Android:
1. Connect to same WiFi as server
2. Open Chrome or Firefox
3. Go to: `http://your-server-ip:8000`
4. Login/register
5. Full app experience!

### Features on Mobile:
✅ Score tracking  
✅ Leaderboard  
✅ Seat arrangement  
✅ Trend charts  
✅ Real-time updates  
✅ Touch-friendly interface  

---

## 🏗️ System Architecture

```
Accounting System
├── Backend (FastAPI + Python)
│   ├── Endpoints (HTTP API)
│   ├── WebSocket (real-time)
│   └── SQLite Database
├── Frontend (HTML/CSS/JS)
│   ├── Responsive design
│   ├── Mobile-friendly
│   └── Real-time updates
└── Data Storage
    ├── score_system.db (SQLite)
    ├── data/users.json (backup)
    ├── data/seats/ (history)
    └── data/sessions/ (archive)
```

---

## 🔐 Security

- ✅ Per-user authentication (login required)
- ✅ Username/password validation
- ✅ Admin-only functions protected
- ✅ Data properly encoded (UTF-8)
- ✅ SQL injection protection (parameterized queries)
- ⚠️ Not HTTPS (use for local/trusted networks only)
- ⚠️ No external internet access recommended

---

## 📊 API Endpoints

### Public Endpoints
- `GET /` - Web app
- `POST /register` - Register new user
- `POST /login` - Login
- `GET /api/users` - Active users list
- `GET /api/scores` - Leaderboard
- `GET /api/system_info` - IP & access info
- `GET /api/trends` - Trend data
- `WS /ws/{username}` - Real-time updates

### Admin Endpoints
- `POST /api/reset_all` - Delete everything
- `POST /api/new_session` - Create new session
- `POST /api/delete_user` - Deactivate user
- `POST /api/reactivate_user` - Reactivate user
- `GET /api/users_all` - All users including inactive

---

## 🐛 Troubleshooting

### Can't connect from other devices?
1. Check both on same WiFi
2. Check IP address is correct
3. Check firewall allows port 8000
4. Verify server is running: `curl http://localhost:8000`

See [WIFI_SETUP.md#troubleshooting](WIFI_SETUP.md#troubleshooting) for detailed help.

### Port 8000 already in use?
```bash
# Find and kill process
lsof -i :8000
kill -9 <PID>

# Or use different port
python main.py --port 8001
```

### Import errors?
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

More help: See [SETUP_GUIDE.md#troubleshooting](SETUP_GUIDE.md#troubleshooting)

---

## 📚 Documentation Files Overview

| File | Purpose | Length | Time |
|------|---------|--------|------|
| **QUICK_REFERENCE.md** | Fast one-page reference | ~300 lines | 2 min |
| **WIFI_SETUP.md** | Network setup guide | ~400 lines | 5 min |
| **SETUP_GUIDE.md** | Complete setup manual | ~400 lines | 15 min |
| **CHANGES_SUMMARY.md** | Version 2.0 changes | ~300 lines | 5 min |
| **README.md** (original) | App overview | varies | varies |

---

## 🎯 Recommended Reading Order

### For First Time Users:
1. This file (2 min)
2. QUICK_REFERENCE.md (2 min)
3. Start playing! (5 min)

### For Network Setup:
1. QUICK_REFERENCE.md (2 min)
2. WIFI_SETUP.md (5 min)
3. Get IP and share URL (2 min)

### For Deployment:
1. SETUP_GUIDE.md - Local Setup section (5 min)
2. Follow installation steps (10 min)
3. SETUP_GUIDE.md - Deployment section (10 min)

### For Admin Tasks:
1. QUICK_REFERENCE.md - Admin Functions (2 min)
2. Login as admin (peng)
3. Use admin buttons in UI

---

## 🚀 Getting Help

### Error: Can't reach server
- Check: `curl http://localhost:8000/`
- See: [SETUP_GUIDE.md#troubleshooting](SETUP_GUIDE.md#troubleshooting)

### Error: Other devices can't connect
- Check: `curl http://localhost:8000/api/system_info`
- See: [WIFI_SETUP.md#troubleshooting](WIFI_SETUP.md#troubleshooting)

### Error: Module not found
- Solution: `pip install -r requirements.txt`
- See: [SETUP_GUIDE.md#installation-steps](SETUP_GUIDE.md#installation-steps)

### Need to reset everything
- Use: Admin reset button or API
- See: [QUICK_REFERENCE.md#admin-functions](QUICK_REFERENCE.md#admin-functions)

### Want to deploy elsewhere
- See: [SETUP_GUIDE.md#deployment-to-another-machine](SETUP_GUIDE.md#deployment-to-another-machine)

---

## ✨ Key Features

### Core Features
- 🎲 Real-time score tracking
- 📊 Live leaderboard ranking
- 💰 Buy-in/cash-out tracking
- 🎯 Win/loss recording
- 📈 Trend charts and analytics
- 🪑 Automatic seat arrangement
- 📱 Mobile-friendly interface

### Admin Features
- 👥 User management
- 🔄 Session management
- 🔁 Score rebalancing
- 🗑️ Complete data reset
- 📊 User activity logging
- 🛡️ Admin-only controls

### New in Version 2.0
- ✅ Chinese character usernames (小明, 张三, etc.)
- ✅ Network access (WiFi support for multiple devices)
- ✅ Safe data reset with confirmations
- ✅ System info API for easy setup
- ✅ Comprehensive setup documentation
- ✅ WiFi network guide

---

## 📋 Checklist for First Setup

- [ ] Read this file
- [ ] Read QUICK_REFERENCE.md
- [ ] Install Python 3.8+
- [ ] Install dependencies: `pip install fastapi uvicorn python-multipart`
- [ ] Start server: `python main.py`
- [ ] Open browser: `http://localhost:8000`
- [ ] Register with username (can be Chinese!)
- [ ] Play and track scores!
- [ ] (Optional) Get IP and share with others: `curl http://localhost:8000/api/system_info`

---

## 🎉 Ready to Go!

You're all set! Choose your path:

- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** ← Start playing now!
- **[WIFI_SETUP.md](WIFI_SETUP.md)** ← Setup network access
- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** ← Detailed setup & deployment
- **[CHANGES_SUMMARY.md](CHANGES_SUMMARY.md)** ← What's new?

Happy accounting! 🎲🎉

---

**Version:** 2.0  
**Last Updated:** 2026-03-17  
**Status:** Fully documented and ready to use ✅
