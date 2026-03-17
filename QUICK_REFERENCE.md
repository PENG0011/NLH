# Accounting System - Quick Reference Card

## 🚀 Quick Start

### 1️⃣ First Time Setup (macOS/Linux)
```bash
cd ranking
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn python-multipart
python main.py
```

### 2️⃣ Open in Browser
```
http://localhost:8000
```

### 3️⃣ Register & Login
- Create new account (supports Chinese characters: 中文用户名 ✅)
- Choose unique emoji avatar
- Login

---

## 📱 WiFi Network Access

### Get Access URL:
```bash
# While server is running, get system info
curl http://localhost:8000/api/system_info
```

**Output example:**
```json
{
  "access_url": "http://192.168.1.100:8000"
}
```

### Share with Other Devices:
1. Give them the `access_url` (e.g., `http://192.168.1.100:8000`)
2. They must be on the same WiFi network
3. They open that URL in their browser

### Find Your IP if API Doesn't Work:
```bash
# macOS
ifconfig | grep "inet " | grep -v 127

# Linux
hostname -I

# Windows
ipconfig
```

---

## 🎮 Features

### Scorekeeping
- **Buy In**: Add money to the game
- **Cash Out**: Remove money from game
- **Set Current**: Manually set chip count
- **Win/Loss**: Record hand wins/losses against another player

### Leaderboard
- Real-time ranking by win/loss
- View: Current chips, Buy-in amount, Profit/Loss
- Rebalance scores to ensure accuracy
- Undo recent rebalances

### Seat Arrangement
- Auto-generate random seating
- View player avatars and positions
- Mirror table view (rotate 180°) for visibility

### Trends
- Real-time win/loss trend chart
- Track each player's progression
- Historical data view

---

## 🔧 Admin Functions

### Login as Admin
- Username: `peng` (or any user marked as admin)

### Admin Panel (in Points tab)
1. **新建游戏会话** - Create new game session (archives current scores)
2. **刷新数据** - Refresh all display data
3. **管理用户** - Manage users (activate/deactivate accounts)
4. **⚠️ 清空所有数据** - DELETE all users and game data (irreversible!)

### User Management
- Deactivate/reactivate players
- Users disappear from leaderboard when deactivated
- Reactivate to restore

---

## 💾 Data Location

```
ranking/
├── main.py                 # Main application
├── score_system.db        # SQLite database (all data)
├── data/
│   ├── users.json         # User list backup
│   ├── seats/             # Seat arrangement history
│   └── sessions/          # Game session archives
├── templates/
│   └── index.html         # Web interface
├── static/                # Assets
└── SETUP_GUIDE.md        # Full setup documentation
```

---

## 🛠️ Common Commands

| Task | Command |
|------|---------|
| Start server | `python main.py` |
| Start with 4 workers | `uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4` |
| Get system info | `curl http://localhost:8000/api/system_info` |
| Backup database | `cp score_system.db score_system.db.backup` |
| Check if port 8000 is free | `lsof -i :8000` (macOS/Linux) |
| Find your local IP | `hostname -I` or `ifconfig` |

---

## 📋 API Endpoints

### Public
- `GET /` - Main app
- `POST /register` - Register new user
- `POST /login` - Login
- `GET /api/users` - Active users list
- `GET /api/scores` - Leaderboard
- `GET /api/system_info` - IP & port info

### Admin Only
- `POST /api/reset_all` - Delete all data ⚠️
- `POST /api/new_session` - Create new session
- `POST /api/delete_user` - Deactivate user
- `POST /api/reactivate_user` - Reactivate user

### WebSocket
- `WS /ws/{username}` - Real-time updates

---

## 🚨 Troubleshooting

**Can't connect from other devices?**
```bash
# 1. Check server is running on 0.0.0.0
# 2. Verify firewall allows port 8000
# 3. Verify both devices on same WiFi
# 4. Check IP address is correct (use /api/system_info)
```

**Port 8000 already in use?**
```bash
# Find what's using it
lsof -i :8000

# Use different port
uvicorn main:app --port 8001 --host 0.0.0.0
```

**Module not found?**
```bash
# Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

**Database locked?**
```bash
# Restart the server
# Ctrl+C to stop, then run again
python main.py
```

---

## 🎯 Chinese Character Support

Username now fully supports Chinese characters! Examples:
- ✅ 小明 (Xiaoming)
- ✅ 张三 (Zhang San)  
- ✅ 中文用户 (Chinese User)
- ✅ Mixed: abc中文123

Avatars remain emoji only (50+ unique options).

---

## 📦 Deployment Examples

### Same Network (Already done!)
```bash
python main.py  # Accessible from http://<your-ip>:8000
```

### Another Machine
```bash
# Copy the ranking folder to the target machine
scp -r ranking user@host:/home/user/

# SSH into host and run:
cd ranking
pip install fastapi uvicorn python-multipart
python main.py
```

### Docker
```bash
docker build -t accounting .
docker run -p 8000:8000 -v accounting-data:/app/data accounting
```

---

## ⚡ Performance Tips

1. Use production mode for multiple players:
   ```bash
   uvicorn main:app --workers 4 --host 0.0.0.0 --port 8000
   ```

2. Regular backups:
   ```bash
   cp score_system.db score_system.db.backup-$(date +%Y%m%d)
   ```

3. Monitor performance:
   - Check system logs for errors
   - Watch for database lock messages

---

## 📞 Support

- Full guide: See `SETUP_GUIDE.md`
- Admin issues: Check admin panel in Points tab
- API issues: Check logs in terminal
- Network issues: Run `/api/system_info` to debug

---

## 🎉 You're Ready!

```bash
python main.py
# → http://localhost:8000
# → Share http://<your-ip>:8000 with other devices!
```

Enjoy! 🎲
