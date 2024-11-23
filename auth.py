# auth.py

import json
import hashlib
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_USERS = {
    "deepika@1acre.in": "deepika@1acre",
    "sandeep@1acre.in": "1acre@sandeep",
    "satish@1acre.in": "1acre@satish",
    "pavan@1acre.in": "1acre@pavan",
    "rohith@montaigne.co": "montaigne@rohith"
}

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def initialize_default_users() -> bool:
    try:
        users = {email: hash_password(password) 
                for email, password in DEFAULT_USERS.items()}
        with open('users.json', 'w') as f:
            json.dump(users, f, indent=4)
        logger.info(f"Initialized {len(users)} default users")
        return True
    except Exception as e:
        logger.error(f"Error initializing default users: {e}")
        return False

def load_users() -> dict:
    try:
        # Check if users.json exists, if not initialize it
        if not os.path.exists('users.json'):
            logger.warning("users.json not found, initializing default users")
            initialize_default_users()
        
        with open('users.json', 'r') as f:
            users = json.load(f)
            logger.info(f"Loaded {len(users)} users")
            return users
    except Exception as e:
        logger.error(f"Error loading users: {e}")
        # If any error occurs, reinitialize
        if initialize_default_users():
            return load_users()
        return {}

def save_users(users: dict) -> bool:
    try:
        with open('users.json', 'w') as f:
            json.dump(users, f, indent=4)
        return True
    except Exception as e:
        logger.error(f"Error saving users: {e}")
        return False

def authenticate(username: str, password: str) -> bool:
    try:
        users = load_users()
        if not users:
            # If no users exist, initialize defaults
            initialize_default_users()
            users = load_users()
        
        hashed_password = hash_password(password)
        is_valid = username in users and users[username] == hashed_password
        
        if is_valid:
            logger.info(f"Successful login: {username}")
        else:
            logger.warning(f"Failed login attempt: {username}")
        
        return is_valid
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        return False

def register_user(username: str, password: str) -> bool:
    try:
        users = load_users()
        if username in users:
            return False
        
        users[username] = hash_password(password)
        return save_users(users)
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return False

# Initialize users on module import
if not os.path.exists('users.json'):
    initialize_default_users()