"""
Authentication and Authorization Module for QKD Dashboard

Handles user login, role management, and permission validation.
"""

import hashlib
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
import hmac

class User:
    """Represents a dashboard user with role and permissions"""
    
    def __init__(self, username: str, role: str, hashed_password: str):
        self.username = username
        self.role = role  # 'admin' or 'user'
        self.hashed_password = hashed_password
        self.last_login = None
        self.session_token = None
    
    def verify_password(self, password: str) -> bool:
        """Verify password against hash"""
        return hashlib.sha256(password.encode()).hexdigest() == self.hashed_password


class AuthManager:
    """Manages user authentication and authorization"""
    
    # Default users (in production, use a database)
    # Set these variables in the deployment platform. The fallback values make
    # local development work, but must not be used on an Internet-facing app.
    DEFAULT_USERS = {
        'admin': {
            'password_hash': hashlib.sha256(
                os.getenv('QKD_ADMIN_PASSWORD', 'admin@qkd2026').encode()
            ).hexdigest(),
            'role': 'admin'
        },
        'user': {
            'password_hash': hashlib.sha256(
                os.getenv('QKD_USER_PASSWORD', 'user@qkd2026').encode()
            ).hexdigest(),
            'role': 'user'
        }
    }
    
    PERMISSIONS = {
        'admin': {
            'view_dashboard': True,
            'view_logs': True,
            'view_settings': True,
            'modify_settings': True,
            'start_nodes': True,
            'stop_nodes': True,
            'simulate_attack': True,
            'export_data': True,
            'manage_users': True,
            'view_keystores': True,
        },
        'user': {
            'view_dashboard': True,
            'view_logs': True,
            'view_settings': True,
            'modify_settings': False,
            'start_nodes': False,
            'stop_nodes': False,
            'simulate_attack': False,
            'export_data': True,
            'manage_users': False,
            'view_keystores': False,
        }
    }
    
    def __init__(self):
        self.users = self._load_users()
        self.sessions = {}  # session_token -> (username, expiry)
    
    def _load_users(self) -> Dict[str, User]:
        """Load users from file or use defaults"""
        users_file = os.path.join(os.path.dirname(__file__), '.users.json')
        
        if os.path.exists(users_file):
            try:
                with open(users_file, 'r') as f:
                    data = json.load(f)
                    return {
                        username: User(username, info['role'], info['password_hash'])
                        for username, info in data.items()
                    }
            except Exception as e:
                print(f"Error loading users: {e}")
        
        # Use defaults
        return {
            username: User(username, info['role'], info['password_hash'])
            for username, info in self.DEFAULT_USERS.items()
        }
    
    def _save_users(self):
        """Save users to file"""
        users_file = os.path.join(os.path.dirname(__file__), '.users.json')
        data = {
            username: {
                'role': user.role,
                'password_hash': user.hashed_password
            }
            for username, user in self.users.items()
        }
        try:
            with open(users_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving users: {e}")
    
    def authenticate(self, username: str, password: str) -> Tuple[bool, Optional[str], str]:
        """
        Authenticate user and create session
        Returns: (success, session_token, message)
        """
        user = self.users.get(username)
        
        if not user:
            return False, None, "Invalid username or password"
        
        if not user.verify_password(password):
            return False, None, "Invalid username or password"
        
        # Create session token
        session_token = hashlib.sha256(
            f"{username}{datetime.now().isoformat()}".encode()
        ).hexdigest()
        
        expiry = datetime.now() + timedelta(hours=24)
        self.sessions[session_token] = (username, expiry)
        
        user.last_login = datetime.now()
        
        return True, session_token, f"Welcome, {username}!"
    
    def verify_session(self, session_token: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Verify if session token is valid
        Returns: (valid, username)
        """
        if not session_token or session_token not in self.sessions:
            return False, None
        
        username, expiry = self.sessions[session_token]
        
        if datetime.now() > expiry:
            del self.sessions[session_token]
            return False, None
        
        return True, username
    
    def get_user_role(self, username: str) -> Optional[str]:
        """Get user's role"""
        user = self.users.get(username)
        return user.role if user else None
    
    def has_permission(self, username: str, action: str) -> bool:
        """Check if user has permission for action"""
        role = self.get_user_role(username)
        if not role:
            return False
        
        permissions = self.PERMISSIONS.get(role, {})
        return permissions.get(action, False)
    
    def create_user(self, username: str, password: str, role: str = 'user') -> Tuple[bool, str]:
        """Create a new user (admin only)"""
        if username in self.users:
            return False, "User already exists"
        
        if role not in ['admin', 'user']:
            return False, "Invalid role"
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        self.users[username] = User(username, role, password_hash)
        self._save_users()
        
        return True, f"User '{username}' created successfully"
    
    def delete_user(self, username: str) -> Tuple[bool, str]:
        """Delete a user (admin only)"""
        if username not in self.users:
            return False, "User not found"
        
        if username in ['admin', 'user']:
            return False, "Cannot delete default users"
        
        del self.users[username]
        self._save_users()
        
        return True, f"User '{username}' deleted"
    
    def logout(self, session_token: str) -> bool:
        """Logout user"""
        if session_token in self.sessions:
            del self.sessions[session_token]
            return True
        return False


# Global auth manager instance
_auth_manager = None

def get_auth_manager() -> AuthManager:
    """Get or create global auth manager"""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager
