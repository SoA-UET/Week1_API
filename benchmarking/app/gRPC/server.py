"""
gRPC Server Implementation
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import grpc
from concurrent import futures
import time

# Import generated protobuf files
try:
    import user_service_pb2
    import user_service_pb2_grpc
except ImportError as e:
    print(f"Protobuf files not found: {e}")
    print("Please generate them by running:")
    print("cd app/gRPC && python -m grpc_tools.protoc --proto_path=proto --python_out=. --grpc_python_out=. proto/user_service.proto")
    sys.exit(1)

from common.utils import DataLoader
from common.models import User as UserModel

class UserServiceServicer(user_service_pb2_grpc.UserServiceServicer):
    """gRPC User Service implementation"""
    
    def __init__(self):
        self.users_db = {}
        self.next_id = 1
        self.initialize_data()
    
    def initialize_data(self):
        """Load initial data from CSV"""
        try:
            csv_path = Path(__file__).parent.parent / "common" / "data" / "users.csv"
            loader = DataLoader(str(csv_path))
            users = loader.load_users()
            
            for user in users:
                self.users_db[user.id] = user
                self.next_id = max(self.next_id, user.id + 1)
            
            print(f"Loaded {len(users)} users from CSV")
        except Exception as e:
            print(f"Error loading data: {e}")
    
    def GetUsers(self, request, context):
        """Get all users with pagination"""
        user_list = list(self.users_db.values())[request.skip:request.skip + request.limit]
        
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
        user = self.users_db.get(request.user_id)
        
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
        user = UserModel(id=self.next_id, name=request.name, email=request.email)
        self.users_db[self.next_id] = user
        self.next_id += 1
        
        return user_service_pb2.CreateUserResponse(
            user=user_service_pb2.User(
                id=user.id,
                name=user.name,
                email=user.email
            ),
            success=True
        )
    
    def UpdateUser(self, request, context):
        """Update an existing user"""
        user = self.users_db.get(request.user_id)
        
        if not user:
            return user_service_pb2.UpdateUserResponse(success=False)
        
        if request.name:
            user.name = request.name
        if request.email:
            user.email = request.email
        
        return user_service_pb2.UpdateUserResponse(
            user=user_service_pb2.User(
                id=user.id,
                name=user.name,
                email=user.email
            ),
            success=True
        )
    
    def DeleteUser(self, request, context):
        """Delete a user"""
        user = self.users_db.get(request.user_id)
        
        if not user:
            return user_service_pb2.DeleteUserResponse(
                success=False,
                message="User not found"
            )
        
        deleted_user = self.users_db.pop(request.user_id)
        return user_service_pb2.DeleteUserResponse(
            success=True,
            message=f"User {deleted_user.name} deleted successfully"
        )
    
    def SearchUsers(self, request, context):
        """Search users by name or email"""
        results = []
        query_lower = request.query.lower()
        
        for user in self.users_db.values():
            if (query_lower in user.name.lower() or 
                query_lower in user.email.lower()):
                results.append(user_service_pb2.User(
                    id=user.id,
                    name=user.name,
                    email=user.email
                ))
        
        return user_service_pb2.SearchUsersResponse(users=results)

def serve():
    """Start the gRPC server"""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    user_service_pb2_grpc.add_UserServiceServicer_to_server(
        UserServiceServicer(), server
    )
    
    port = '50051'
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    
    print(f"gRPC Server started on port {port}")
    print(f"Total users loaded: {len(UserServiceServicer().users_db)}")
    
    try:
        while True:
            time.sleep(86400)  # Keep server running
    except KeyboardInterrupt:
        print("Shutting down gRPC server...")
        server.stop(0)

if __name__ == '__main__':
    serve()