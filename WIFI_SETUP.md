# WiFi Network Setup - Device Access Guide

## Overview

The Accounting system can be accessed by multiple devices on the same WiFi network. Follow this guide to set up network access.

---

## ✅ Prerequisites

- ✅ Accounting system is running: `python main.py`
- ✅ Your machine (server) connected to WiFi
- ✅ Other devices connected to the **same WiFi network**
- ✅ Port 8000 not blocked by firewall

---

## Step 1: Get Your Server's IP Address

### Method A: Using the App (Easiest)

While the server is running:

```bash
curl http://localhost:8000/api/system_info
```

Look for the `access_url` field. Example response:

```json
{
  "local_ip": "192.168.1.100",
  "port": 8000,
  "access_url": "http://192.168.1.100:8000",
  "note": "Share this URL with other devices on the same WiFi network"
}
```

**Your access URL is:** `http://192.168.1.100:8000` (replace IP with your actual IP)

---

### Method B: Manual - macOS

```bash
# Option 1: Using ifconfig (most reliable)
ifconfig | grep "inet " | grep -v 127.0.0.1
```

**Output example:**
```
inet 192.168.1.100 netmask 0xffffff00 broadcast 192.168.1.255
inet 127.0.0.1 netmask 0xff000000 broadcast 127.0.0.1  (← ignore this)
```

Your IP is: **192.168.1.100**

```bash
# Option 2: Using hostname
hostname -I
```

### Method B: Manual - Linux

```bash
# Option 1: Using hostname
hostname -I

# Option 2: Using ip command
ip addr show | grep "inet " | grep -v 127.0.0.1
```

### Method B: Manual - Windows

```cmd
# Open Command Prompt and run:
ipconfig

# Look for "IPv4 Address" (usually 192.168.x.x or 10.x.x.x)
```

---

## Step 2: Share the Access URL

Once you have your IP address, construct the URL:

```
http://<YOUR_IP>:8000
```

**Examples:**
- `http://192.168.1.100:8000`
- `http://10.0.0.50:8000`
- `http://192.168.0.1:8000`

---

## Step 3: Access from Another Device

### On the client device (phone, tablet, laptop):

1. **Connect to the same WiFi network**
   - Go to WiFi settings
   - Select the same network as the server machine

2. **Open a web browser** (Chrome, Safari, Firefox, Edge, etc.)

3. **Enter the access URL**
   - Type: `http://192.168.1.100:8000` (use YOUR actual IP)
   - Press Enter

4. **You should see the login page!**
   - Register with your name (中文 Chinese characters supported ✅)
   - Choose an emoji avatar
   - Start playing!

---

## 📱 Example Scenarios

### Scenario 1: Playing on iPhone

1. Host (MacBook):
   - Running: `python main.py`
   - IP: `192.168.1.100`

2. Client (iPhone):
   - Connected to same WiFi
   - Safari → `http://192.168.1.100:8000`
   - See login page ✅

### Scenario 2: Multiple Players

1. One machine running the server
2. Multiple devices (phones, tablets, laptops) all connected to same WiFi
3. All access `http://<server-ip>:8000`
4. All see real-time updates (scores, leaderboard, seat arrangements)

### Scenario 3: Android Device

1. Open Chrome
2. Go to `http://192.168.1.100:8000`
3. Works the same as desktop!

---

## 🔥 Troubleshooting

### "Can't reach the server" / "Connection refused"

**Check 1: Is the server running?**
```bash
# On the server machine, make sure you see:
# INFO:     Uvicorn running on http://0.0.0.0:8000

# If not, restart:
python main.py
```

**Check 2: Are you using the correct IP?**
```bash
# Re-run to verify:
curl http://localhost:8000/api/system_info
```

**Check 3: Are you on the same WiFi?**
- Check settings on client device
- Should say connected to the same network name as server

**Check 4: Is your firewall blocking port 8000?**

**macOS:**
- System Preferences → Security & Privacy → Firewall Options
- Add Python or allow port 8000

**Windows:**
```
Settings → Firewall & Network Protection → 
Allow an app through firewall → 
Add Python executable or port 8000
```

**Linux:**
```bash
# Allow port 8000
sudo ufw allow 8000/tcp
```

### "Connection took too long"

1. Check server is actually listening:
   ```bash
   curl http://localhost:8000
   ```
   Should show HTML (the app page)

2. Ping from client to verify network connectivity:
   ```bash
   ping 192.168.1.100  # replace with your actual IP
   ```

3. Try with port explicitly:
   ```
   http://192.168.1.100:8000/
   ```

### Other devices can't connect but you can locally

**This usually means:**
1. Server not listening on all interfaces
2. Firewall is blocking
3. IP address is wrong

**Solution:**
1. Verify using API:
   ```bash
   curl http://localhost:8000/api/system_info
   ```

2. Ensure started with `--host 0.0.0.0`:
   ```bash
   # This is the default when you run:
   python main.py
   
   # Or explicitly:
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

3. Check firewall is allowing port 8000 (see above)

---

## 🔒 Network Security

### For Local WiFi Only (Recommended)

If you only trust devices on your home WiFi:
- ✅ Current setup is fine
- Just share IP with trusted devices

### For Internet Access

If you want to allow access from outside your WiFi:

1. **Port forwarding** (advanced):
   - Configure router to forward external port to 8000
   - But not recommended without authentication

2. **VPN** (more secure):
   - Set up VPN tunnel
   - Only devices with VPN can access

3. **Authentication** (recommended):
   - Current system uses username/password ✅
   - Users must login to access any data

### What NOT to Do

❌ Don't expose to internet without HTTPS  
❌ Don't use simple/default passwords  
❌ Don't allow public access without authentication  

---

## 📊 Network Topology

```
┌─────────────────────────────────────────┐
│          WiFi Network (192.168.1.x)     │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────────────────────────┐  │
│  │   Server Machine (192.168.1.100) │  │
│  │   python main.py                 │  │
│  │   Listening on 0.0.0.0:8000      │  │
│  └──────────────────────────────────┘  │
│            ↑                            │
│    ┌───────┼───────┬─────────┐         │
│    │       │       │         │         │
│    ▼       ▼       ▼         ▼         │
│  iPhone  Android  Laptop   Tablet     │
│  Safari  Chrome   Safari   Firefox    │
│  Client1 Client2  Client3  Client4   │
│                                       │
│  All access: http://192.168.1.100:8000│
└─────────────────────────────────────────┘

All connected devices see:
✅ Real-time leaderboard updates
✅ Live seat arrangements  
✅ Activity logs
✅ Trend charts
```

---

## 🚀 Advanced: Static IP for Your Server

For consistency, you might want a static IP for your server machine:

### macOS:

1. System Preferences → Network
2. Advanced → TCP/IP
3. Set "IPv4 Configuration" to "Manual"
4. Assign a static IP (e.g., 192.168.1.100)
5. Click OK

### Linux:

Edit `/etc/netplan/01-netcfg.yaml`:
```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: no
      addresses: [192.168.1.100/24]
      gateway4: 192.168.1.1
      nameservers:
        addresses: [8.8.8.8, 8.8.4.4]
```

Then apply:
```bash
sudo netplan apply
```

### Windows:

1. Settings → Network & Internet → WiFi → Change Adapter Options
2. Right-click network → Properties
3. IPv4 Properties
4. Set IP manually (192.168.1.100 etc.)

---

## 📖 Next Steps

1. ✅ Get your IP from `/api/system_info`
2. ✅ Share URL with other devices: `http://your.ip:8000`
3. ✅ Others register and login
4. ✅ Start playing!

---

## 💡 Tips

- **Broadcast IP via QR Code**: Use a QR code generator to create a QR for your URL, share with players
- **Simplify IP**: Write IP on whiteboard/paper near the table
- **Bookmark**: Tell players to bookmark the URL for quick access
- **Status**: Check `/api/system_info` anytime to get current URL

---

## ✨ Features Work Perfectly on Mobile

- ✅ Responsive design (works on phones)
- ✅ Touch-friendly buttons
- ✅ WebSocket real-time updates
- ✅ Full leaderboard view
- ✅ Seat arrangement display
- ✅ Score tracking

---

## 🆘 Still Having Issues?

1. **Verify server running:**
   ```bash
   curl http://localhost:8000/
   ```

2. **Check system info:**
   ```bash
   curl http://localhost:8000/api/system_info
   ```

3. **Verify firewall:**
   - Try allowing "Python" in firewall settings
   - Or explicitly allow port 8000

4. **Network diagnostic:**
   ```bash
   # From client machine
   ping 192.168.1.100
   nc -zv 192.168.1.100 8000
   ```

5. **Check logs:**
   - Terminal where you ran `python main.py` shows all requests
   - Look for errors or connection messages

---

## 🎮 Ready to Play!

Your accounting system is now network-accessible! Share the URL with your friends and start tracking scores together. 🎲🎉
