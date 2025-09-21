"""
Simple gRPC Server Implementation
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import grpc
from concurrent import futures
import time
from common.simple_utils import DataLoader, User as UserModel

# Try to import protobuf files
try:
    # Add the gRPC directory to sys.path
    grpc_dir = str(Path(__file__).parent)
    if grpc_dir not in sys.path:
        sys.path.insert(0, grpc_dir)
    
    import user_service_pb2
    import user_service_pb2_grpc
    GRPC_AVAILABLE = True
except ImportError:
    GRPC_AVAILABLE = False
    print("gRPC protobuf files not found. Generate them with:")
    print("cd app/gRPC && python -m grpc_tools.protoc --proto_path=proto --python_out=. --grpc_python_out=. proto/user_service.proto")

# Global data storage
users_db = {}
next_id = 1

def initialize_data():
    """Load initial data from CSV"""
    global next_id
    try:
        csv_path = Path(__file__).parent.parent / "common" / "data" / "users.csv"
        loader = DataLoader(str(csv_path))
        users = loader.load_users()
        
        for user in users:
            users_db[user.id] = user
            next_id = max(next_id, user.id + 1)
        
        print(f"gRPC: Loaded {len(users)} users from CSV")
    except Exception as e:
        print(f"gRPC: Error loading data: {e}")

class UserServiceServicer(user_service_pb2_grpc.UserServiceServicer):
    """gRPC User Service implementation"""
    
    def GetUsers(self, request, context):
        """Get all users with pagination"""
        user_list = list(users_db.values())[request.skip:request.skip + request.limit]
        
        users = []
        for user in user_list:
            users.append(user_service_pb2.User(
                id=user.id,
                name=user.name,
                email=user.email
            ))
        
        return user_service_pb2.GetUsersResponse(users=users)
    
    def GetUser(self, request, context):
        """Get user by ID"""
        user = users_db.get(request.user_id)
        
        if user:
            return user_service_pb2.GetUserResponse(
                user=user_service_pb2.User(
                    id=user.id,
                    name=user.name,
                    email=user.email
                ),
                found=True
            )
        else:
            return user_service_pb2.GetUserResponse(found=False)
    
    def CreateUser(self, request, context):
        """Create a new user"""
        global next_id
        user = UserModel(id=next_id, name=request.name, email=request.email)
        users_db[next_id] = user
        next_id += 1
        
        return user_service_pb2.CreateUserResponse(
            user=user_service_pb2.User(
                id=user.id,
                name=user.name,
                email=user.email
            ),
            success=True
        )

def serve():
    """Start the gRPC server"""
    if not GRPC_AVAILABLE:
        print("Cannot start gRPC server - protobuf files not available")
        return None
    
    initialize_data()
    
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    user_service_pb2_grpc.add_UserServiceServicer_to_server(
        UserServiceServicer(), server
    )
    
    port = '50051'
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    
    print(f"gRPC Server started on port {port}")
    print(f"Total users loaded: {len(users_db)}")
    
    return server

if __name__ == '__main__':
    server = serve()
    if server:
        try:
            while True:
                time.sleep(86400)  # Keep server running
        except KeyboardInterrupt:
            print("Shutting down gRPC server...")
            server.stop(0)