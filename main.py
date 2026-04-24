import json
import random
import math
import sqlite3
import os
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# 初始化FastAPI应用
app = FastAPI()

# 静态文件和模板配置
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 可用的唯一 Emoji 头像列表
EMOJI_AVATARS = [
    '🐶','🐱','🐭','🐹','🐰','🦊','🐻','🐼','🐨','🐯',
    '🦁','🐮','🐷','🐸','🐵','🐔','🐧','🐦','🐤','🦆',
    '🦅','🦉','🦇','🐺','🦄','🐝','🐛','🦋','🐌','🐞',
    '🐢','🐍','🦖','🦕','🐙','🦑','🦐','🦞','🐬','🐳',
    '🐋','🦈','🐠','🐟','🐊','🦣','🐘','🐐','🐏','🐑',
    '🦒','🦓','🦍','🦧','🐘','🦛','🦏','🐪','🐫','🦒',
    '🦘','🐃','🐂','🐄','🐎','🐖','🐏','🐑','🦉','🦅',
    '🦆','🦢','🦜','🦚','🦃','🦚','🦜','🦢','🦆','🕊️',
    '🐓','🐔','🐤','🐣','🐥','🦆','🦅','🦉','🦇','🐺',
    '🐗','🐴','🦄','🐝','🐛','🦋','🐌','🐞','🐜','🦟'
]

# 数据库初始化
def init_db():
    conn = sqlite3.connect("score_system.db")
    cursor = conn.cursor()
    
    # 用户表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        avatar TEXT DEFAULT 'default_avatar.png',
        is_admin BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 游戏会话表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS game_sessions (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 记分表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS scores (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        session_id TEXT NOT NULL,
        brought REAL DEFAULT 0,
        current REAL DEFAULT 0,
        win_loss REAL DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (session_id) REFERENCES game_sessions(id)
    )
    ''')

    # 记分历史表（用于趋势图）
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS score_history (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        session_id TEXT NOT NULL,
        current REAL NOT NULL,
        win_loss REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (session_id) REFERENCES game_sessions(id)
    )
    ''')
    
    # 不再预先创建默认用户，用户将自行注册
    
    conn.commit()
    conn.close()

    # ensure users table has an `active` column for soft-deletes
    try:
        cur = sqlite3.connect("score_system.db")
        cur_row = cur.cursor()
        # check if column exists
        cols = [r[1] for r in cur_row.execute("PRAGMA table_info(users)").fetchall()]
        if 'active' not in cols:
            cur_row.execute("ALTER TABLE users ADD COLUMN active INTEGER DEFAULT 1")
            cur.commit()
        cur.close()
    except Exception:
        # non-fatal if alter fails
        pass

init_db()

# Data directory helpers and JSON persistence
DATA_DIR = "data"
SESSIONS_DIR = os.path.join(DATA_DIR, "sessions")
SEATS_DIR = os.path.join(DATA_DIR, "seats")
USERS_FILE = os.path.join(DATA_DIR, "users.json")

def ensure_data_dirs():
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    os.makedirs(SEATS_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)

ensure_data_dirs()

def save_users_file():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT username, avatar, is_admin, created_at, active FROM users")
    rows = cur.fetchall()
    conn.close()
    users = []
    for r in rows:
        try:
            active_val = bool(r["active"])
        except Exception:
            active_val = True
        users.append({
            "username": r["username"],
            "avatar": r["avatar"],
            "is_admin": bool(r["is_admin"]),
            "active": active_val,
            "created_at": r["created_at"]
        })
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def create_session_file(session_id: str, name: str):
    ensure_data_dirs()
    session_obj = {
        "id": session_id,
        "name": name,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "scores": []
    }
    path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(session_obj, f, ensure_ascii=False, indent=2)
    return path

def save_seats_file(session_id: str, seats, mirror=False):
    ensure_data_dirs()
    ts = int(time.time())
    obj = {
        "session_id": session_id,
        "seats": seats,
        "mirror": bool(mirror),
        "generated_at": datetime.utcnow().isoformat() + "Z"
    }
    latest_path = os.path.join(SEATS_DIR, f"{session_id}_latest.json")
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    archive_path = os.path.join(SEATS_DIR, f"{session_id}_{ts}.json")
    with open(archive_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    return latest_path, archive_path

# WebSocket连接管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}  # username: websocket

    async def connect(self, websocket: WebSocket, username: str):
        await websocket.accept()
        self.active_connections[username] = websocket
        # 广播用户上线
        await self.broadcast({
            "type": "user_status",
            "action": "online",
            "username": username,
            "online_users": list(self.active_connections.keys())
        })

    def disconnect(self, username: str):
        if username in self.active_connections:
            del self.active_connections[username]
            # 广播用户下线
            self.broadcast_sync({
                "type": "user_status",
                "action": "offline",
                "username": username,
                "online_users": list(self.active_connections.keys())
            })

    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_text(json.dumps(message))

    def broadcast_sync(self, message: dict):
        import asyncio
        asyncio.create_task(self.broadcast(message))

manager = ConnectionManager()

# 保存最近一次生成的座位分配（内存存储）
last_seats = []

# Pydantic模型
class UserCreate(BaseModel):
    username: str
    avatar: Optional[str] = "default_avatar.png"

class ScoreUpdate(BaseModel):
    username: str
    action: str  # buy_in, cash_out, set_current, win, loss
    amount: float
    target_user: Optional[str] = None

class RebalanceRequest(BaseModel):
    count: int

class SeatGenerateRequest(BaseModel):
    usernames: List[str]

# 辅助函数
def get_db_connection():
    conn = sqlite3.connect("score_system.db")
    conn.row_factory = sqlite3.Row
    return conn

def get_user_by_username(username: str) -> Optional[dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    if user:
        user_dict = dict(user)
        # "peng" is always super admin
        if username.lower() == 'peng':
            user_dict['is_admin'] = True
        return user_dict
    return None

def get_or_create_default_session() -> str:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM game_sessions WHERE name = 'Default Session'")
    session = cursor.fetchone()
    if session:
        session_id = session["id"]
    else:
        session_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO game_sessions (id, name) VALUES (?, ?)",
            (session_id, "Default Session")
        )
        conn.commit()
        try:
            # create a session json file for persistence
            create_session_file(session_id, "Default Session")
        except Exception:
            pass
    conn.close()
    return session_id

def get_user_score(username: str, session_id: str) -> dict:
    user = get_user_by_username(username)
    if not user:
        return None
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM scores WHERE user_id = ? AND session_id = ?",
        (user["id"], session_id)
    )
    score = cursor.fetchone()
    if not score:
        # 创建默认记分记录
        score_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO scores (id, user_id, session_id, brought, current, win_loss) VALUES (?, ?, ?, 0, 0, 0)",
            (score_id, user["id"], session_id)
        )
        conn.commit()
        cursor.execute("SELECT * FROM scores WHERE id = ?", (score_id,))
        score = cursor.fetchone()
    conn.close()
    return dict(score)

def update_user_score(username: str, session_id: str, updates: dict):
    user = get_user_by_username(username)
    if not user:
        return False
    
    score = get_user_score(username, session_id)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
    values = list(updates.values()) + [score["id"]]
    
    cursor.execute(
        f"UPDATE scores SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        values
    )
    conn.commit()
    # 插入一条历史记录，记录更新后的 current 和 win_loss
    cursor.execute("SELECT current, win_loss FROM scores WHERE id = ?", (score["id"],))
    cur_row = cursor.fetchone()
    try:
        history_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO score_history (id, user_id, session_id, current, win_loss) VALUES (?, ?, ?, ?, ?)",
            (history_id, user["id"], session_id, cur_row["current"], cur_row["win_loss"])
        )
        conn.commit()
    except Exception:
        # 忽略历史写入错误，不影响主流程
        pass
    conn.close()
    return True


def get_trends(session_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT u.username, h.current, h.win_loss, h.created_at
    FROM score_history h
    JOIN users u ON h.user_id = u.id
    WHERE h.session_id = ?
    ORDER BY h.created_at ASC
    ''', (session_id,))

    rows = cursor.fetchall()
    conn.close()

    # 组织为每个用户的时间序列
    trends = {}
    for row in rows:
        uname = row["username"]
        if uname not in trends:
            trends[uname] = []
        trends[uname].append({
            "timestamp": row["created_at"],
            "current": row["current"],
            "win_loss": row["win_loss"]
        })
    return trends

# API路由
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/register")
async def register(user: UserCreate):
    if get_user_by_username(user.username):
        return JSONResponse({"success": False, "message": "用户名已存在"})

    # 如果选择的是 Emoji 头像，确保唯一性
    avatar_choice = user.avatar or 'default_avatar.png'
    if avatar_choice in EMOJI_AVATARS:
        # 检查是否被其他用户占用
        conn_chk = get_db_connection()
        cur_chk = conn_chk.cursor()
        cur_chk.execute("SELECT username FROM users WHERE avatar = ?", (avatar_choice,))
        exists = cur_chk.fetchone()
        conn_chk.close()
        if exists:
            return JSONResponse({"success": False, "message": "该表情已被其他用户选择，请选择其他头像"})
    
    user_id = str(uuid.uuid4())
    # 自动将用户名为 peng 的账号设置为管理员
    is_admin_flag = 1 if user.username and user.username.lower() == 'peng' else 0
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (id, username, avatar, is_admin) VALUES (?, ?, ?, ?)",
        (user_id, user.username, user.avatar, is_admin_flag)
    )
    conn.commit()
    conn.close()
    
    # 为新用户创建默认会话的记分记录
    session_id = get_or_create_default_session()
    update_user_score(user.username, session_id, {"brought": 0, "current": 0, "win_loss": 0})
    # persist users to JSON file
    try:
        save_users_file()
    except Exception:
        pass
    
    return JSONResponse({"success": True, "message": "注册成功"})


@app.get('/api/avatars')
async def api_avatars():
    # 返回所有可用的 emoji 列表和已被占用的列表
    conn = get_db_connection()
    cursor = conn.cursor()
    # only consider active users for taken avatars
    cursor.execute("SELECT avatar FROM users WHERE active != 0 AND avatar IN ({})".format(
        ','.join('?' for _ in EMOJI_AVATARS)
    ), EMOJI_AVATARS)
    rows = cursor.fetchall()
    taken = [r['avatar'] for r in rows]
    conn.close()
    return {"all": EMOJI_AVATARS, "taken": taken}


@app.get('/api/users_all')
async def api_users_all():
    """Return all users including inactive with their active flag."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username, avatar, active, is_admin FROM users")
    users = []
    for row in cursor.fetchall():
        try:
            active_val = bool(row["active"])
        except Exception:
            active_val = True
        try:
            is_admin_val = bool(row["is_admin"])
        except Exception:
            is_admin_val = False
        # "peng" is always admin
        if row["username"].lower() == "peng":
            is_admin_val = True
        users.append({"username": row["username"], "avatar": row["avatar"], "active": active_val, "is_admin": is_admin_val})
    conn.close()
    return {"users": users}


@app.post('/api/toggle_admin')
async def api_toggle_admin(request: Request):
    """Toggle admin status for a user. Only peng can do this."""
    payload = await request.json()
    admin_user = payload.get('admin_user', '')
    target_user = payload.get('username', '')
    
    # Only "peng" can assign admin status
    if admin_user.lower() != 'peng':
        return JSONResponse({"success": False, "message": "只有 peng 可以进行此操作"})
    
    if not target_user:
        return JSONResponse({"success": False, "message": "用户名必填"})
    
    # Can't remove peng's admin status
    if target_user.lower() == 'peng':
        return JSONResponse({"success": False, "message": "无法更改 peng 的管理员状态"})
    
    target = get_user_by_username(target_user)
    if not target:
        return JSONResponse({"success": False, "message": "用户不存在"})
    
    # Toggle admin status
    conn = get_db_connection()
    cur = conn.cursor()
    current_admin = bool(target.get('is_admin', 0))
    new_admin_status = 0 if current_admin else 1
    cur.execute("UPDATE users SET is_admin = ? WHERE username = ?", (new_admin_status, target_user))
    conn.commit()
    conn.close()
    
    # Save users file
    try:
        save_users_file()
    except Exception:
        pass
    
    action = "升级为" if new_admin_status else "降级为"
    await manager.broadcast({"type": "admin_status_changed", "username": target_user, "is_admin": bool(new_admin_status)})
    return {"success": True, "message": f"已{action}管理员", "is_admin": bool(new_admin_status)}


@app.post('/api/reactivate_user')
async def api_reactivate_user(request: Request):
    try:
        payload = await request.json()
    except:
        return JSONResponse({"success": False, "message": "invalid JSON"})
    admin_user = payload.get('admin_user')
    target = payload.get('username')
    if not admin_user or not target:
        return JSONResponse({"success": False, "message": "admin_user and username required"})
    admin = get_user_by_username(admin_user)
    if not admin or not admin.get('is_admin'):
        return JSONResponse({"success": False, "message": "only admins can reactivate users"})

    user = get_user_by_username(target)
    if not user:
        return JSONResponse({"success": False, "message": "user not found"})

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET active = 1 WHERE username = ?", (target,))
    conn.commit()
    conn.close()

    try:
        save_users_file()
    except Exception:
        pass

    await manager.broadcast({"type": "user_status", "action": "reactivated", "username": target})
    return {"success": True}


@app.post('/api/update_avatar')
async def api_update_avatar(payload: dict):
    username = payload.get('username')
    avatar = payload.get('avatar')
    if not username or avatar is None:
        return JSONResponse({"success": False, "message": "invalid payload"})

    user = get_user_by_username(username)
    if not user:
        return JSONResponse({"success": False, "message": "user not found"})

    # If avatar is an emoji, ensure uniqueness except for the current user
    if avatar in EMOJI_AVATARS:
        conn_chk = get_db_connection()
        cur_chk = conn_chk.cursor()
        cur_chk.execute("SELECT username FROM users WHERE avatar = ? AND username != ?", (avatar, username))
        exists = cur_chk.fetchone()
        conn_chk.close()
        if exists:
            return JSONResponse({"success": False, "message": "该表情已被其他用户选择"})

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET avatar = ? WHERE username = ?", (avatar, username))
    conn.commit()
    conn.close()

    # persist users json
    try:
        save_users_file()
    except Exception:
        pass

    # 广播头像更改
    await manager.broadcast({"type": "user_status", "action": "avatar_change", "username": username, "avatar": avatar})
    return JSONResponse({"success": True})

@app.post("/login")
async def login(username: str = Form()):
    user = get_user_by_username(username)
    if not user:
        return JSONResponse({"success": False, "message": "用户不存在"})
    
    token = str(uuid.uuid4())
    return JSONResponse({
        "success": True,
        "token": token,
        "user": {
            "username": user["username"],
            "avatar": user["avatar"],
            "is_admin": user["is_admin"]
        }
    })

@app.get("/api/users")
async def get_all_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username, avatar FROM users WHERE active != 0")
    users = [{"username": row["username"], "avatar": row["avatar"]} for row in cursor.fetchall()]
    conn.close()
    return {"users": users}

@app.get("/api/scores")
async def get_all_scores():
    session_id = get_or_create_default_session()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT u.username, s.brought, s.current, s.win_loss
    FROM scores s
    JOIN users u ON s.user_id = u.id
    WHERE s.session_id = ? AND u.active != 0
    ''', (session_id,))
    scores = []
    total_win_loss = 0
    for row in cursor.fetchall():
        score = {
            "player": row["username"],
            "brought": row["brought"],
            "current": row["current"],
            "win_loss": row["win_loss"]
        }
        scores.append(score)
        total_win_loss += row["win_loss"]
    
    # 按win_loss排序
    scores.sort(key=lambda x: x["win_loss"], reverse=True)
    conn.close()
    return {"scores": scores, "total_win_loss": total_win_loss}

@app.post("/api/update_score")
async def update_score(data: ScoreUpdate):
    session_id = get_or_create_default_session()
    user_score = get_user_score(data.username, session_id)
    if not user_score:
        return {"success": False, "message": "用户不存在"}
    
    updates = {}
    if data.action == "buy_in":
        updates["brought"] = user_score["brought"] + data.amount
        updates["current"] = user_score["current"] + data.amount
    elif data.action == "cash_out":
        # cashing out reduces both the buy-in (brought) and the current balance
        new_brought = max(0, user_score.get("brought", 0) - data.amount)
        new_current = max(0, user_score.get("current", 0) - data.amount)
        updates["brought"] = new_brought
        updates["current"] = new_current
        # adjust win_loss accordingly (current - brought)
        updates["win_loss"] = new_current - new_brought
    elif data.action == "set_current":
        updates["current"] = data.amount
        updates["win_loss"] = data.amount - user_score["brought"]
    elif data.action == "win":
        if not data.target_user:
            return {"success": False, "message": "请选择输家"}
        
        # 赢家增加金额
        updates["current"] = user_score["current"] + data.amount
        updates["win_loss"] = user_score["win_loss"] + data.amount
        
        # 输家减少金额
        target_score = get_user_score(data.target_user, session_id)
        if target_score:
            update_user_score(
                data.target_user,
                session_id,
                {
                    "current": target_score["current"] - data.amount,
                    "win_loss": target_score["win_loss"] - data.amount
                }
            )
    elif data.action == "loss":
        if not data.target_user:
            return {"success": False, "message": "请选择赢家"}
        
        # 输家减少金额
        updates["current"] = user_score["current"] - data.amount
        updates["win_loss"] = user_score["win_loss"] - data.amount
        
        # 赢家增加金额
        target_score = get_user_score(data.target_user, session_id)
        if target_score:
            update_user_score(
                data.target_user,
                session_id,
                {
                    "current": target_score["current"] + data.amount,
                    "win_loss": target_score["win_loss"] + data.amount
                }
            )
    
    update_user_score(data.username, session_id, updates)
    
    # 广播记分更新
    await manager.broadcast({
        "type": "score_update",
        "username": data.username,
        "action": data.action,
        "amount": data.amount
    })
    
    return {"success": True}

@app.post("/api/rebalance")
async def rebalance(data: RebalanceRequest):
    session_id = get_or_create_default_session()
    scores = await get_all_scores()
    total_win_loss = scores["total_win_loss"]
    if abs(total_win_loss) < 0.01:  # 误差范围内视为0
        return {"success": True, "message": "无需重新平衡"}

    # 分离赢家和输家
    winners = [s for s in scores["scores"] if s["win_loss"] > 0]
    losers = [s for s in scores["scores"] if s["win_loss"] < 0]

    # Helper: random split of amount into n positive parts summing to total
    def random_split(total, n):
        if n <= 0:
            return []
        weights = [random.random() for _ in range(n)]
        s = sum(weights)
        if s == 0:
            return [total / n] * n
        return [total * (w / s) for w in weights]

    if total_win_loss < 0:
        # 总和为负：可以让输家少输 -> 按输的最多（最负）排序，给若干输家随机加分
        amount_needed = -total_win_loss
        losers.sort(key=lambda x: x["win_loss"])  # most negative first
        selected = losers[: max(1, min(len(losers), data.count))]
        if not selected:
            return {"success": False, "message": "没有可调整的输家"}

        deltas = random_split(amount_needed, len(selected))
        for loser, delta in zip(selected, deltas):
            new_win = loser["win_loss"] + delta
            new_current = max(0, loser["current"] + delta)
            update_user_score(loser["player"], session_id, {"win_loss": new_win, "current": new_current})
    else:
        # 总和为正：需要让赢家少赢 -> 按赢的最多排序，给若干赢家随机减分
        amount_needed = total_win_loss
        winners.sort(key=lambda x: x["win_loss"], reverse=True)
        selected = winners[: max(1, min(len(winners), data.count))]
        if not selected:
            return {"success": False, "message": "没有可调整的赢家"}

        deltas = random_split(amount_needed, len(selected))
        for winner, delta in zip(selected, deltas):
            # subtract delta from winner
            new_win = winner["win_loss"] - delta
            new_current = max(0, winner["current"] - delta)
            update_user_score(winner["player"], session_id, {"win_loss": new_win, "current": new_current})
    
    await manager.broadcast({"type": "rebalance", "message": "已完成重新平衡"})
    return {"success": True}

@app.post("/api/generate_seats")
async def generate_seats(request: Request):
    """Generate a NLH-style table seating arrangement.

    Request body (optional JSON): { "count": <table_size> }
    Default table size is 9 (standard NLH full-ring). All registered users will be
    seated randomly up to the table size. Empty seats are returned as username=None.
    """
    body = {}
    try:
        body = await request.json()
    except Exception:
        body = {}

    # ignore explicit count; seat all registered users evenly around the table
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE active != 0")
    usernames = [row["username"] for row in cursor.fetchall() if row["username"]]
    conn.close()

    if not usernames:
        return {"seats": []}

    # Reserve mj at top (index 0) or bottom (index mid) if present
    mj_username = None
    remaining = []
    for u in usernames:
        if u.lower() == 'mj':
            mj_username = u
        else:
            remaining.append(u)

    random.shuffle(remaining)

    table_size = len(usernames)
    seats = [None] * table_size

    def place_username_at(index, name):
        if 0 <= index < table_size:
            seats[index] = {"seat": index + 1, "username": name}

    if mj_username:
        mid_index = table_size // 2
        # mj always assigned logical top (index 0) on server side; mirror flag will
        # instruct client to flip the table visually ~50% of the time so mj appears bottom
        place_username_at(0, mj_username)

    ri = 0
    for i in range(table_size):
        if seats[i] is not None:
            continue
        place_username_at(i, remaining[ri])
        ri += 1

    # compute angle for each seat so frontend can place them exactly as server intends
    seats_with_angle = []
    for i, s in enumerate(seats):
        angle = (2 * math.pi * i) / table_size - math.pi / 2
        seats_with_angle.append({
            "seat": s["seat"],
            "username": s["username"],
            "angle": angle
        })

    # decide mirror randomly (~50%) — when mirror is true the client will rotate
    # the table 180deg, which places logical top at visual bottom.
    mirror = random.random() < 0.5

    response = {"seats": seats_with_angle, "mirror": mirror}
    # persist seats to file for the current session
    try:
        session_id = get_or_create_default_session()
        save_seats_file(session_id, seats_with_angle, mirror)
        response = {"seats": seats_with_angle, "mirror": mirror, "session_id": session_id}
    except Exception:
        response = {"seats": seats_with_angle, "mirror": mirror}

    global last_seats
    last_seats = response
    await manager.broadcast({"type": "seats_update", "seats": seats_with_angle, "mirror": mirror})
    return response


@app.get('/api/seats')
async def get_seats():
    # 返回最近一次生成的座位分配（如果没有则返回空列表）
    # `last_seats` may be either a dict (response from generate_seats)
    # or a raw list (older behavior). Normalize to a consistent shape:
    if isinstance(last_seats, dict):
        # already has keys like 'seats' and 'mirror'
        return last_seats
    else:
        return {"seats": last_seats, "mirror": False}

@app.post("/api/coin_flip")
async def coin_flip(percentage: float = Form()):
    # 生成随机结果
    random_num = random.uniform(0, 100)
    result = "yes" if random_num <= percentage else "no"
    
    await manager.broadcast({
        "type": "coin_flip",
        "percentage": percentage,
        "result": result
    })
    return {"success": True, "result": result}


@app.post('/api/new_session')
async def api_new_session(payload: dict):
    """Admin endpoint: create a new game session, persist current session data,
    reset scores for active users to zero, and clear the seat draw."""
    admin_user = payload.get('admin_user')
    name = payload.get('name') or f"Session {datetime.utcnow().isoformat()}"
    if not admin_user:
        return JSONResponse({"success": False, "message": "admin_user required"})

    admin = get_user_by_username(admin_user)
    if not admin or not admin.get('is_admin'):
        return JSONResponse({"success": False, "message": "only admins can create sessions"})

    # persist current session scores to a session file
    try:
        current_session = get_or_create_default_session()
        # export scores for current_session
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
        SELECT u.username, s.brought, s.current, s.win_loss
        FROM scores s
        JOIN users u ON s.user_id = u.id
        WHERE s.session_id = ?
        ''', (current_session,))
        rows = cur.fetchall()
        conn.close()
        session_obj = {
            "id": current_session,
            "name": name,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "scores": [
                {"player": r['username'], "brought": r['brought'], "current": r['current'], "win_loss": r['win_loss']} for r in rows
            ]
        }
        # write to sessions dir
        ensure_data_dirs()
        path = os.path.join(SESSIONS_DIR, f"{current_session}.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(session_obj, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    # create a brand new session and make it the 'Default Session'
    conn = get_db_connection()
    cur = conn.cursor()

    # If there is an existing 'Default Session', archive it by renaming
    cur.execute("SELECT id FROM game_sessions WHERE name = 'Default Session'")
    existing = cur.fetchone()
    if existing:
        try:
            archive_name = f"Archived Session {int(time.time())}"
            cur.execute("UPDATE game_sessions SET name = ? WHERE id = ?", (archive_name, existing[0]))
        except Exception:
            pass

    # insert the new session as the active Default Session
    new_session_id = str(uuid.uuid4())
    cur.execute("INSERT INTO game_sessions (id, name) VALUES (?, ?)", (new_session_id, 'Default Session'))
    conn.commit()

    # For each active user, initialize scores for the new session to zero
    cur.execute("SELECT id, username FROM users WHERE active != 0")
    users = cur.fetchall()
    for u in users:
        score_id = str(uuid.uuid4())
        cur.execute(
            "INSERT INTO scores (id, user_id, session_id, brought, current, win_loss) VALUES (?, ?, ?, 0, 0, 0)",
            (score_id, u['id'], new_session_id)
        )
    conn.commit()
    conn.close()

    # clear last seats
    global last_seats
    last_seats = {"seats": [], "mirror": False}

    # create session json
    try:
        create_session_file(new_session_id, name)
    except Exception:
        pass

    # notify clients to reload
    await manager.broadcast({"type": "new_session", "session_id": new_session_id})
    return {"success": True, "session_id": new_session_id}


@app.post('/api/delete_user')
async def api_delete_user(request: Request):
    """Admin endpoint: mark a user inactive so they no longer appear in leaderboard or seat draws."""
    try:
        payload = await request.json()
    except:
        return JSONResponse({"success": False, "message": "invalid JSON"})
    admin_user = payload.get('admin_user')
    target = payload.get('username')
    if not admin_user or not target:
        return JSONResponse({"success": False, "message": "admin_user and username required"})
    admin = get_user_by_username(admin_user)
    if not admin or not admin.get('is_admin'):
        return JSONResponse({"success": False, "message": "only admins can delete users"})

    user = get_user_by_username(target)
    if not user:
        return JSONResponse({"success": False, "message": "user not found"})

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET active = 0 WHERE username = ?", (target,))
    conn.commit()
    conn.close()

    # persist users
    try:
        save_users_file()
    except Exception:
        pass

    # broadcast user inactive
    await manager.broadcast({"type": "user_status", "action": "deactivated", "username": target})
    return {"success": True}


@app.get("/api/trends")
async def api_trends():
    session_id = get_or_create_default_session()
    trends = get_trends(session_id)
    return {"trends": trends}

@app.post('/api/reset_all')
async def api_reset_all(payload: dict):
    """Admin endpoint: delete all users and reset all game data."""
    admin_user = payload.get('admin_user')
    if not admin_user:
        return JSONResponse({"success": False, "message": "admin_user required"})
    
    admin = get_user_by_username(admin_user)
    if not admin or not admin.get('is_admin'):
        return JSONResponse({"success": False, "message": "only admins can reset all data"})
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Delete all data
        cur.execute("DELETE FROM score_history")
        cur.execute("DELETE FROM scores")
        cur.execute("DELETE FROM users")
        cur.execute("DELETE FROM game_sessions")
        
        conn.commit()
        conn.close()
        
        # Reinitialize database
        init_db()
        
        # Clear persisted data files
        try:
            import shutil
            if os.path.exists(USERS_FILE):
                os.remove(USERS_FILE)
            if os.path.exists(SESSIONS_DIR):
                shutil.rmtree(SESSIONS_DIR)
            if os.path.exists(SEATS_DIR):
                shutil.rmtree(SEATS_DIR)
            ensure_data_dirs()
        except Exception as e:
            print(f"Warning: could not delete some data files: {e}")
        
        # Reset global state
        global last_seats
        last_seats = {"seats": [], "mirror": False}
        
        # Broadcast reset to all connected clients
        await manager.broadcast({"type": "system_reset", "message": "All data has been reset"})
        
        return {"success": True, "message": "所有数据已删除，系统已重置"}
    except Exception as e:
        print(f"Reset failed: {e}")
        return {"success": False, "message": f"重置失败: {str(e)}"}

@app.get('/api/system_info')
async def api_system_info():
    """Return system information for setup guidance (IP address, port, etc)."""
    import socket
    try:
        # Get local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        local_ip = "127.0.0.1"
    
    return {
        "local_ip": local_ip,
        "port": 8000,
        "access_url": f"http://{local_ip}:8000",
        "note": "Share this URL with other devices on the same WiFi network"
    }

# WebSocket路由
@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await manager.connect(websocket, username)
    try:
        while True:
            data = await websocket.receive_text()
            # 处理客户端消息（如果需要）
            await manager.broadcast({
                "type": "user_message",
                "username": username,
                "message": data
            })
    except WebSocketDisconnect:
        manager.disconnect(username)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)