import os
import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

# Route database file to /tmp on Vercel serverless environments
DB_PATH = "/tmp/pocketsmart.db" if os.getenv("VERCEL") else os.path.join(os.path.dirname(os.path.abspath(__file__)), "pocketsmart.db")

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        hashed_password TEXT NOT NULL,
        full_name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # Recommendations table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recommendations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        category TEXT NOT NULL,
        title TEXT NOT NULL,
        input_parameters TEXT NOT NULL,
        result_data TEXT NOT NULL,
        total_budget REAL NOT NULL,
        allocated_budget REAL NOT NULL,
        image_path TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );
    """)
    
    conn.commit()
    conn.close()

def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE LOWER(username) = LOWER(?)", (username,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE LOWER(email) = LOWER(?)", (email,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def create_user(username: str, email: str, hashed_password: str, full_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, email, hashed_password, full_name) VALUES (?, ?, ?, ?)",
            (username.strip(), email.strip().lower(), hashed_password, full_name.strip() if full_name else username.strip())
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return get_user_by_id(user_id)
    except sqlite3.IntegrityError:
        conn.close()
        return None

def save_recommendation(
    user_id: Optional[int],
    category: str,
    title: str,
    input_params: Dict[str, Any],
    result_data: Dict[str, Any],
    total_budget: float,
    allocated_budget: float,
    image_path: Optional[str] = None
) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO recommendations 
        (user_id, category, title, input_parameters, result_data, total_budget, allocated_budget, image_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            category,
            title,
            json.dumps(input_params),
            json.dumps(result_data),
            float(total_budget),
            float(allocated_budget),
            image_path
        )
    )
    conn.commit()
    rec_id = cursor.lastrowid
    conn.close()
    return rec_id

def get_recommendations(user_id: Optional[int] = None, category: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM recommendations WHERE 1=1"
    params = []
    
    if user_id is not None:
        query += " AND user_id = ?"
        params.append(user_id)
        
    if category and category.lower() != 'all':
        query += " AND category = ?"
        params.append(category.lower())
        
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for r in rows:
        item = dict(r)
        try:
            item["input_parameters"] = json.loads(item["input_parameters"])
        except Exception:
            pass
        try:
            item["result_data"] = json.loads(item["result_data"])
        except Exception:
            pass
        results.append(item)
    return results

def get_recommendation_by_id(rec_id: int, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if user_id is not None:
        cursor.execute("SELECT * FROM recommendations WHERE id = ? AND user_id = ?", (rec_id, user_id))
    else:
        cursor.execute("SELECT * FROM recommendations WHERE id = ?", (rec_id,))
        
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    item = dict(row)
    try:
        item["input_parameters"] = json.loads(item["input_parameters"])
    except Exception:
        pass
    try:
        item["result_data"] = json.loads(item["result_data"])
    except Exception:
        pass
    return item

def delete_recommendation(rec_id: int, user_id: Optional[int] = None) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    if user_id is not None:
        cursor.execute("DELETE FROM recommendations WHERE id = ? AND user_id = ?", (rec_id, user_id))
    else:
        cursor.execute("DELETE FROM recommendations WHERE id = ?", (rec_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def get_user_stats(user_id: int) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*), COALESCE(SUM(total_budget), 0), COALESCE(SUM(allocated_budget), 0) FROM recommendations WHERE user_id = ?", (user_id,))
    total_plans, total_budget_sum, total_allocated_sum = cursor.fetchone()
    
    cursor.execute("SELECT category, COUNT(*) as cnt FROM recommendations WHERE user_id = ? GROUP BY category ORDER BY cnt DESC LIMIT 1", (user_id,))
    top_cat = cursor.fetchone()
    favorite_category = top_cat[0] if top_cat else "None yet"
    
    conn.close()
    return {
        "total_plans": total_plans,
        "total_budget_sum": total_budget_sum,
        "total_allocated_sum": total_allocated_sum,
        "favorite_category": favorite_category.capitalize() if favorite_category != "None yet" else "None yet"
    }

# Initialize database on module load
init_db()
