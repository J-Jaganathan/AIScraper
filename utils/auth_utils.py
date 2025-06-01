import bcrypt
import streamlit as st
from pymongo import MongoClient
from datetime import datetime, timedelta
import os
from typing import Optional, Dict, List
import secrets
from dotenv import load_dotenv
load_dotenv()

class AuthManager:
    def __init__(self):
        # MongoDB connection
        mongo_uri = os.getenv("MONGODB_URI") or st.secrets.get("MONGODB_URI", "mongodb://localhost:27017/")
        self.client = MongoClient(mongo_uri)
        self.db = self.client.ai_scraper
        self.users_collection = self.db.users
        self.sessions_collection = self.db.sessions
        self.scrapes_collection = self.db.scrapes
        
        # Create indexes
        self.users_collection.create_index("username", unique=True)
        self.users_collection.create_index("email", unique=True)
        self.sessions_collection.create_index("session_token", unique=True)
        self.sessions_collection.create_index("expires_at")
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def create_user(self, username: str, email: str, password: str, is_admin: bool = False) -> Dict:
        """Create new user"""
        try:
            # Check if user exists
            if self.users_collection.find_one({"$or": [{"username": username}, {"email": email}]}):
                return {"success": False, "message": "Username or email already exists"}
            
            # Create user document
            user_doc = {
                "username": username,
                "email": email,
                "password_hash": self.hash_password(password),
                "is_admin": is_admin,
                "created_at": datetime.utcnow(),
                "last_login": None,
                "total_scrapes": 0
            }
            
            result = self.users_collection.insert_one(user_doc)
            return {
                "success": True, 
                "message": "User created successfully",
                "user_id": str(result.inserted_id)
            }
        except Exception as e:
            return {"success": False, "message": f"Error creating user: {str(e)}"}
    
    def authenticate_user(self, username: str, password: str) -> Dict:
        """Authenticate user and create session"""
        try:
            user = self.users_collection.find_one({"username": username})
            if not user:
                return {"success": False, "message": "Invalid username or password"}
            
            if not self.verify_password(password, user["password_hash"]):
                return {"success": False, "message": "Invalid username or password"}
            
            # Update last login
            self.users_collection.update_one(
                {"_id": user["_id"]},
                {"$set": {"last_login": datetime.utcnow()}}
            )
            
            # Create session
            session_token = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(hours=24)
            
            session_doc = {
                "user_id": user["_id"],
                "session_token": session_token,
                "expires_at": expires_at,
                "created_at": datetime.utcnow()
            }
            
            self.sessions_collection.insert_one(session_doc)
            
            return {
                "success": True,
                "message": "Login successful",
                "session_token": session_token,
                "user": {
                    "id": str(user["_id"]),
                    "username": user["username"],
                    "email": user["email"],
                    "is_admin": user.get("is_admin", False)
                }
            }
        except Exception as e:
            return {"success": False, "message": f"Authentication error: {str(e)}"}
    
    def verify_session(self, session_token: str) -> Optional[Dict]:
        """Verify session token and return user info"""
        try:
            session = self.sessions_collection.find_one({
                "session_token": session_token,
                "expires_at": {"$gt": datetime.utcnow()}
            })
            
            if not session:
                return None
            
            user = self.users_collection.find_one({"_id": session["user_id"]})
            if not user:
                return None
            
            return {
                "id": str(user["_id"]),
                "username": user["username"],
                "email": user["email"],
                "is_admin": user.get("is_admin", False)
            }
        except Exception as e:
            st.error(f"Session verification error: {str(e)}")
            return None
    
    def logout(self, session_token: str) -> bool:
        """Delete session token"""
        try:
            self.sessions_collection.delete_one({"session_token": session_token})
            return True
        except:
            return False
    
    def get_user_scrapes(self, user_id: str) -> List[Dict]:
        """Get all scrapes for a user"""
        try:
            scrapes = list(self.scrapes_collection.find(
                {"user_id": user_id}
            ).sort("created_at", -1))
            
            for scrape in scrapes:
                scrape["_id"] = str(scrape["_id"])
            
            return scrapes
        except Exception as e:
            st.error(f"Error fetching scrapes: {str(e)}")
            return []
    
    def save_scrape_result(self, user_id: str, prompt: str, website: str, 
                          results: List[Dict], status: str = "completed") -> str:
        """Save scrape result to database"""
        try:
            scrape_doc = {
                "user_id": user_id,
                "prompt": prompt,
                "website": website,
                "results": results,
                "status": status,
                "created_at": datetime.utcnow(),
                "record_count": len(results)
            }
            
            result = self.scrapes_collection.insert_one(scrape_doc)
            
            # Update user's total scrapes
            self.users_collection.update_one(
                {"_id": user_id},
                {"$inc": {"total_scrapes": 1}}
            )
            
            return str(result.inserted_id)
        except Exception as e:
            st.error(f"Error saving scrape: {str(e)}")
            return ""
    
    def get_all_users_admin(self) -> List[Dict]:
        """Get all users (admin only)"""
        try:
            users = list(self.users_collection.find(
                {},
                {"password_hash": 0}  # Exclude password hash
            ).sort("created_at", -1))
            
            for user in users:
                user["_id"] = str(user["_id"])
            
            return users
        except Exception as e:
            st.error(f"Error fetching users: {str(e)}")
            return []
    
    def get_all_scrapes_admin(self) -> List[Dict]:
        """Get all scrapes (admin only)"""
        try:
            pipeline = [
                {
                    "$lookup": {
                        "from": "users",
                        "localField": "user_id",
                        "foreignField": "_id",
                        "as": "user"
                    }
                },
                {
                    "$unwind": "$user"
                },
                {
                    "$project": {
                        "prompt": 1,
                        "website": 1,
                        "status": 1,
                        "created_at": 1,
                        "record_count": 1,
                        "username": "$user.username"
                    }
                },
                {
                    "$sort": {"created_at": -1}
                }
            ]
            
            scrapes = list(self.scrapes_collection.aggregate(pipeline))
            
            for scrape in scrapes:
                scrape["_id"] = str(scrape["_id"])
            
            return scrapes
        except Exception as e:
            st.error(f"Error fetching all scrapes: {str(e)}")
            return []

# Session state management functions
def init_session_state():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'session_token' not in st.session_state:
        st.session_state.session_token = None

def check_authentication():
    """Check if user is authenticated"""
    init_session_state()
    
    if st.session_state.authenticated and st.session_state.session_token:
        auth_manager = AuthManager()
        user = auth_manager.verify_session(st.session_state.session_token)
        
        if user:
            st.session_state.user = user
            return True
        else:
            # Session expired
            st.session_state.authenticated = False
            st.session_state.user = None
            st.session_state.session_token = None
            return False
    
    return False

def login_user(auth_result: Dict):
    """Set user as logged in"""
    if auth_result.get("success"):
        st.session_state.authenticated = True
        st.session_state.user = auth_result["user"]
        st.session_state.session_token = auth_result["session_token"]

def logout_user():
    """Log out current user"""
    if st.session_state.get("session_token"):
        auth_manager = AuthManager()
        auth_manager.logout(st.session_state.session_token)
    
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.session_token = None

def require_auth():
    """Decorator to require authentication"""
    if not check_authentication():
        st.warning("Please log in to access this page.")
        st.stop()

def require_admin():
    """Decorator to require admin privileges"""
    require_auth()
    if not st.session_state.user.get("is_admin", False):
        st.error("Admin access required.")
        st.stop()