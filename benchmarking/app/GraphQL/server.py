"""
GraphQL Server using Ariadne
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from ariadne import QueryType, MutationType, make_executable_schema, graphql_sync
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Optional
from common.models import User as UserModel
from common.utils import DataLoader
import uvicorn
import json

# GraphQL Type Definitions
type_defs = """
    type User {
        id: Int!
        name: String!
        email: String!
    }
    
    input UserInput {
        name: String!
        email: String!
    }
    
    input UserUpdateInput {
        name: String
        email: String
    }
    
    type CreateUserResult {
        user: User
        success: Boolean!
    }
    
    type UpdateUserResult {
        user: User
        success: Boolean!
    }
    
    type DeleteUserResult {
        success: Boolean!
        message: String!
    }
    
    type Query {
        users(skip: Int = 0, limit: Int = 100): [User!]!
        user(userId: Int!): User
        searchUsers(query: String!): [User!]!
    }
    
    type Mutation {
        createUser(userData: UserInput!): CreateUserResult!
        updateUser(userId: Int!, userData: UserUpdateInput!): UpdateUserResult!
        deleteUser(userId: Int!): DeleteUserResult!
    }
"""

# Initialize data storage
users_db = {}
next_id = 1

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

# Initialize query and mutation types
query = QueryType()
mutation = MutationType()

@query.field("users")
def resolve_users(_, info, skip=0, limit=100):
    user_list = list(users_db.values())[skip:skip + limit]
    return [{"id": u.id, "name": u.name, "email": u.email} for u in user_list]

@query.field("user")
def resolve_user(_, info, userId):
    user = users_db.get(userId)
    if user:
        return {"id": user.id, "name": user.name, "email": user.email}
    return None

@query.field("searchUsers")
def resolve_search_users(_, info, query):
    results = []
    query_lower = query.lower()
    
    for user in users_db.values():
        if (query_lower in user.name.lower() or 
            query_lower in user.email.lower()):
            results.append({"id": user.id, "name": user.name, "email": user.email})
    
    return results

@mutation.field("createUser")
def resolve_create_user(_, info, userData):
    global next_id
    user = UserModel(id=next_id, name=userData["name"], email=userData["email"])
    users_db[next_id] = user
    next_id += 1
    
    return {
        "user": {"id": user.id, "name": user.name, "email": user.email},
        "success": True
    }

@mutation.field("updateUser")
def resolve_update_user(_, info, userId, userData):
    user = users_db.get(userId)
    if not user:
        return {"user": None, "success": False}
    
    if "name" in userData and userData["name"]:
        user.name = userData["name"]
    if "email" in userData and userData["email"]:
        user.email = userData["email"]
    
    return {
        "user": {"id": user.id, "name": user.name, "email": user.email},
        "success": True
    }

@mutation.field("deleteUser")
def resolve_delete_user(_, info, userId):
    user = users_db.get(userId)
    if not user:
        return {"success": False, "message": "User not found"}
    
    deleted_user = users_db.pop(userId)
    return {
        "success": True,
        "message": f"User {deleted_user.name} deleted successfully"
    }

# Create executable schema
schema = make_executable_schema(type_defs, query, mutation)

# Create FastAPI app
app = FastAPI(title="GraphQL User Management API")

@app.get("/")
async def root():
    return {
        "message": "GraphQL User Management API", 
        "total_users": len(users_db),
        "graphql_endpoint": "/graphql",
        "playground": "/graphql/playground"
    }

@app.get("/graphql/playground", response_class=HTMLResponse)
async def graphql_playground():
    return PLAYGROUND_HTML

@app.post("/graphql")
async def graphql_server(request: Request):
    data = await request.json()
    success, result = graphql_sync(schema, data)
    status_code = 200 if success else 400
    return JSONResponse(result, status_code=status_code)

@app.on_event("startup")
async def startup_event():
    initialize_data()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)