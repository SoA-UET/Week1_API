"""
Simple GraphQL API Server using Ariadne and FastAPI
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from fastapi import FastAPI
from ariadne import QueryType, MutationType, make_executable_schema
from ariadne.asgi import GraphQL
from typing import List, Optional
from common.models import User, UserCreate
from common.simple_utils import DataLoader
import json

# GraphQL Type Definitions
type_defs = """
    type User {
        id: Int!
        name: String!
        email: String!
    }

    type Query {
        users(limit: Int = 100): [User!]!
        user(id: Int!): User
    }

    type Mutation {
        createUser(name: String!, email: String!): User!
        updateUser(id: Int!, name: String, email: String): User!
        deleteUser(id: Int!): Boolean!
    }
"""

# In-memory storage
users_db = {}
next_id = 1

# Initialize data
def initialize_data():
    global next_id
    try:
        csv_path = Path(__file__).parent.parent / "common" / "data" / "users.csv"
        loader = DataLoader(str(csv_path))
        users = loader.load_users()
        
        for user in users:
            users_db[user.id] = user
            next_id = max(next_id, user.id + 1)
        
        print(f"GraphQL: Loaded {len(users)} users from CSV")
    except Exception as e:
        print(f"GraphQL: Error loading data: {e}")

# Query resolvers
query = QueryType()

@query.field("users")
def resolve_users(_, info, limit=100):
    user_list = list(users_db.values())[:limit]
    return [user.to_dict() for user in user_list]

@query.field("user")
def resolve_user(_, info, id):
    if id in users_db:
        return users_db[id].to_dict()
    return None

# Mutation resolvers
mutation = MutationType()

@mutation.field("createUser")
def resolve_create_user(_, info, name, email):
    global next_id
    
    user = User(id=next_id, name=name, email=email)
    users_db[next_id] = user
    next_id += 1
    
    return user.to_dict()

@mutation.field("updateUser")
def resolve_update_user(_, info, id, name=None, email=None):
    if id not in users_db:
        raise Exception("User not found")
    
    user = users_db[id]
    if name:
        user.name = name
    if email:
        user.email = email
    
    return user.to_dict()

@mutation.field("deleteUser")
def resolve_delete_user(_, info, id):
    if id not in users_db:
        return False
    
    del users_db[id]
    return True

# Create executable schema
schema = make_executable_schema(type_defs, query, mutation)

# FastAPI app
app = FastAPI(title="GraphQL User API")

# Add GraphQL endpoint
graphql_app = GraphQL(schema)
app.mount("/graphql", graphql_app)

@app.on_event("startup")
async def startup_event():
    initialize_data()

@app.get("/")
async def root():
    return {"message": "GraphQL User API", "endpoint": "/graphql", "total_users": len(users_db)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)