import sqlite3
import hashlib
import secrets
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import streamlit as st

class DatabaseManager:
    def __init__(self, db_path: str = "amrita_chatbot.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    roll_number TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    email TEXT,
                    department TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            ''')
            
            # Conversations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    conversation_id TEXT NOT NULL,
                    title TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Messages table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (conversation_id) REFERENCES conversations (id)
                )
            ''')
            
            # Feedback table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    conversation_id TEXT,
                    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
                    comment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Create indexes for better query performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_roll_number ON users(roll_number)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversations_conversation_id ON conversations(conversation_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at DESC)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON feedback(user_id)')
            
            conn.commit()
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256 with salt"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}${password_hash}"
    
    def verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify password against stored hash"""
        try:
            salt, hash_value = stored_hash.split('$')
            password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            return password_hash == hash_value
        except:
            return False
    
    def create_user(self, roll_number: str, password: str, full_name: str, email: str = None, department: str = None) -> Tuple[bool, str]:
        """Create new user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Strip whitespace
                roll_number = roll_number.strip()
                full_name = full_name.strip()
                if email:
                    email = email.strip()
                if department:
                    department = department.strip()
                
                # Check if user already exists
                cursor.execute("SELECT id FROM users WHERE roll_number = ?", (roll_number,))
                if cursor.fetchone():
                    return False, "User with this roll number already exists"
                
                password_hash = self.hash_password(password)
                cursor.execute('''
                    INSERT INTO users (roll_number, password_hash, full_name, email, department)
                    VALUES (?, ?, ?, ?, ?)
                ''', (roll_number, password_hash, full_name, email, department))
                
                conn.commit()
                return True, "User created successfully"
        except Exception as e:
            return False, f"Error creating user: {str(e)}"
    
    def authenticate_user(self, roll_number: str, password: str) -> Tuple[bool, Optional[Dict]]:
        """Authenticate user and return user data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Strip whitespace from roll number
                roll_number = roll_number.strip()
                
                cursor.execute("SELECT * FROM users WHERE roll_number = ?", (roll_number,))
                user = cursor.fetchone()
                
                if not user:
                    print(f"DEBUG: User not found with roll number: '{roll_number}'")
                    return False, None
                
                if self.verify_password(password, user[2]):
                    # Update last login
                    cursor.execute("UPDATE users SET last_login = ? WHERE id = ?", 
                                 (datetime.now(), user[0]))
                    conn.commit()
                    
                    user_data = {
                        'id': user[0],
                        'roll_number': user[1],
                        'full_name': user[3],
                        'email': user[4],
                        'department': user[5],
                        'created_at': user[6],
                        'last_login': user[7]
                    }
                    return True, user_data
                else:
                    print(f"DEBUG: Password verification failed for user: '{roll_number}'")
                    return False, None
        except Exception as e:
            print(f"DEBUG: Exception in authenticate_user: {e}")
            return False, None
    
    def create_conversation(self, user_id: int, conversation_id: str, title: str = None) -> bool:
        """Create new conversation"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO conversations (user_id, conversation_id, title)
                    VALUES (?, ?, ?)
                ''', (user_id, conversation_id, title))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error creating conversation: {e}")
            return False
    
    def save_message(self, conversation_id: str, role: str, content: str) -> bool:
        """Save message to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Get conversation database id
                cursor.execute("SELECT id FROM conversations WHERE conversation_id = ?", (conversation_id,))
                conv = cursor.fetchone()
                
                if conv:
                    cursor.execute('''
                        INSERT INTO messages (conversation_id, role, content)
                        VALUES (?, ?, ?)
                    ''', (conv[0], role, content))
                    
                    # Update conversation updated_at
                    cursor.execute('''
                        UPDATE conversations SET updated_at = ? WHERE conversation_id = ?
                    ''', (datetime.now(), conversation_id))
                    
                    conn.commit()
                    return True
            return False
        except Exception as e:
            print(f"Error saving message: {e}")
            return False
    
    def get_user_conversations(self, user_id: int) -> List[Dict]:
        """Get all conversations for a user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, conversation_id, title, created_at, updated_at, is_active
                    FROM conversations 
                    WHERE user_id = ? 
                    ORDER BY updated_at DESC
                ''', (user_id,))
                
                conversations = []
                for row in cursor.fetchall():
                    conversations.append({
                        'id': row[0],
                        'conversation_id': row[1],
                        'title': row[2],
                        'created_at': row[3],
                        'updated_at': row[4],
                        'is_active': row[5]
                    })
                return conversations
        except Exception as e:
            print(f"Error getting conversations: {e}")
            return []
    
    def get_conversation_messages(self, conversation_id: str) -> List[Dict]:
        """Get all messages for a conversation"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT m.role, m.content, m.timestamp
                    FROM messages m
                    JOIN conversations c ON m.conversation_id = c.id
                    WHERE c.conversation_id = ?
                    ORDER BY m.timestamp ASC
                ''', (conversation_id,))
                
                messages = []
                for row in cursor.fetchall():
                    messages.append({
                        'role': row[0],
                        'content': row[1],
                        'timestamp': row[2]
                    })
                return messages
        except Exception as e:
            print(f"Error getting messages: {e}")
            return []
    
    def save_feedback(self, user_id: int, conversation_id: str, rating: int, comment: str = None) -> bool:
        """Save user feedback"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO feedback (user_id, conversation_id, rating, comment)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, conversation_id, rating, comment))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving feedback: {e}")
            return False
    
    def get_user_feedback_stats(self, user_id: int) -> Dict:
        """Get feedback statistics for a user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT AVG(rating), COUNT(*)
                    FROM feedback
                    WHERE user_id = ?
                ''', (user_id,))
                
                row = cursor.fetchone()
                return {
                    'avg_rating': round(row[0], 2) if row[0] else 0,
                    'total_feedback': row[1] if row[1] else 0
                }
        except Exception as e:
            print(f"Error getting feedback stats: {e}")
            return {'avg_rating': 0, 'total_feedback': 0}

# Initialize database manager
db = DatabaseManager()