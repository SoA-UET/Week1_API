"""
REST API Server using FastAPI
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Optional
from common.models import User, UserCreate, UserUpdate
from common.simple_utils import DataLoader
import uvicorn

app = FastAPI(title="User Management API", version="1.0.0")

# In-memory storage (for benchmarking purposes)
users_db = {}
next_id = 1

# Initialize with data from CSV
def initialize_data():
    global next_id
    try:
        csv_path = Path(__file__).parent.parent / "common" / "data" / "users.csv"
        loader = DataLoader(str(csv_path))
        users = loader.load_users()
        
        for user in users:
            users_db[user.id] = user
            next_id = max(next_id, user.id + 1)
        
        print(f"Loaded {len(users)} users from CSV")
    except Exception as e:
        print(f"Error loading data: {e}")

@app.on_event("startup")
async def startup_event():
    initialize_data()

@app.get("/")
async def root():
    return {"message": "User Management REST API", "total_users": len(users_db)}

@app.get("/users", response_model=List[dict])
async def get_users(skip: int = 0, limit: int = 100):
    """Get all users with pagination"""
    user_list = list(users_db.values())[skip:skip + limit]
    return [user.to_dict() for user in user_list]

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    """Get user by ID"""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    return users_db[user_id].to_dict()

@app.post("/users")
async def create_user(user_data: dict):
    """Create a new user"""
    global next_id
    
    if "name" not in user_data or "email" not in user_data:
        raise HTTPException(status_code=400, detail="Name and email are required")
    
    user = User(id=next_id, name=user_data["name"], email=user_data["email"])
    users_db[next_id] = user
    next_id += 1
    
    return user.to_dict()

@app.put("/users/{user_id}")
async def update_user(user_id: int, user_data: dict):
    """Update an existing user"""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = users_db[user_id]
    if "name" in user_data:
        user.name = user_data["name"]
    if "email" in user_data:
        user.email = user_data["email"]
    
    return user.to_dict()

@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    """Delete a user"""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    deleted_user = users_db.pop(user_id)
    return {"message": f"User {deleted_user.name} deleted successfully"}

@app.get("/users/search/{query}")
async def search_users(query: str):
    """Search users by name or email"""
    results = []
    query_lower = query.lower()
    
    for user in users_db.values():
        if (query_lower in user.name.lower() or 
            query_lower in user.email.lower()):
            results.append(user.to_dict())
    
    return results

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)