# init_users.py

import logging
from auth import hash_password, save_users, verify_users

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def init_users():
    """Initialize users database"""
    try:
        # Define users and passwords
        users = {
            "deepika@1acre.in": hash_password("deepika@1acre"),
            "sandeep@1acre.in": hash_password("1acre@sandeep"),
            "satish@1acre.in": hash_password("1acre@satish"),
            "pavan@1acre.in": hash_password("1acre@pavan"),
            "rohith@montaigne.co": hash_password("montaigne@rohith")
        }
        
        # Save users
        if not save_users(users):
            logger.error("Failed to save users")
            return False
        
        # Verify database
        if not verify_users():
            logger.error("User verification failed")
            return False
        
        logger.info(f"Successfully initialized {len(users)} users")
        return True
        
    except Exception as e:
        logger.error(f"Initialization error: {str(e)}")
        return False

if __name__ == "__main__":
    if init_users():
        print("✅ Users database initialized successfully")
    else:
        print("❌ Failed to initialize users database")
