# utils/user_manager.py
import json
import os

# Always store users.json next to the project root (one level above this file)
_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.normpath(os.path.join(_DIR, '..', 'users.json'))

# Default shape for every user record
_DEFAULT_USER = {
    "games_played": 0,
    "best_score": 0,
    "best_time": None
}

def _ensure_keys(user_dict):
    """Return a copy of user_dict with all required keys present."""
    result = dict(_DEFAULT_USER)   # start with defaults
    result.update(user_dict)       # overwrite with whatever exists
    return result

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            raw = json.load(f)
        # Migrate: ensure every user has all required keys
        migrated = {name: _ensure_keys(data) for name, data in raw.items()}
        return migrated
    except Exception as e:
        print(f"[user_manager] Could not load users.json: {e}")
        return {}

def save_users(users):
    try:
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"[user_manager] Could not save users.json: {e}")

def get_or_create_user(username):
    if not username:
        return dict(_DEFAULT_USER)
    users = load_users()
    if username not in users:
        users[username] = dict(_DEFAULT_USER)
        save_users(users)
    else:
        # Ensure existing user has all keys (migrate old records)
        fixed = _ensure_keys(users[username])
        if fixed != users[username]:
            users[username] = fixed
            save_users(users)
    return users[username]

def update_user_stats(username, score, time_taken):
    if not username:
        return
    users = load_users()
    if username not in users:
        users[username] = dict(_DEFAULT_USER)
    user = users[username]
    user["games_played"] += 1
    if score > user.get("best_score", 0):
        user["best_score"] = score
    bt = user.get("best_time", None)
    if bt is None or time_taken < bt:
        user["best_time"] = time_taken
    save_users(users)
