"""
SOAP Server using Spyne
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from spyne import Application, rpc, ServiceBase, Integer, Unicode, ComplexModel, Array, Boolean
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
from wsgiref.simple_server import make_server
from common.models import User as UserModel
from common.utils import DataLoader

# SOAP Complex Models
class User(ComplexModel):
    id = Integer
    name = Unicode
    email = Unicode

class UserList(ComplexModel):
    users = Array(User)

class CreateUserRequest(ComplexModel):
    name = Unicode
    email = Unicode

class UpdateUserRequest(ComplexModel):
    user_id = Integer
    name = Unicode
    email = Unicode

class DeleteUserResponse(ComplexModel):
    success = Boolean
    message = Unicode

class UserSearchResult(ComplexModel):
    users = Array(User)

class UserService(ServiceBase):
    """SOAP User Service"""
    
    def __init__(self):
        super().__init__()
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
    
    @rpc(Integer, Integer, _returns=UserList)
    def GetUsers(ctx, self, skip=0, limit=100):
        """Get all users with pagination"""
        if not hasattr(self, 'users_db'):
            self.initialize_data()
        
        user_list = list(self.users_db.values())[skip:skip + limit]
        
        users = []
        for user in user_list:
            users.append(User(id=user.id, name=user.name, email=user.email))
        
        return UserList(users=users)
    
    @rpc(Integer, _returns=User)
    def GetUser(ctx, self, user_id):
        """Get user by ID"""
        if not hasattr(self, 'users_db'):
            self.initialize_data()
        
        user = self.users_db.get(user_id)
        if user:
            return User(id=user.id, name=user.name, email=user.email)
        return None
    
    @rpc(Unicode, Unicode, _returns=User)
    def CreateUser(ctx, self, name, email):
        """Create a new user"""
        if not hasattr(self, 'users_db'):
            self.initialize_data()
        
        user = UserModel(id=self.next_id, name=name, email=email)
        self.users_db[self.next_id] = user
        self.next_id += 1
        
        return User(id=user.id, name=user.name, email=user.email)
    
    @rpc(Integer, Unicode, Unicode, _returns=User)
    def UpdateUser(ctx, self, user_id, name=None, email=None):
        """Update an existing user"""
        if not hasattr(self, 'users_db'):
            self.initialize_data()
        
        user = self.users_db.get(user_id)
        if not user:
            return None
        
        if name:
            user.name = name
        if email:
            user.email = email
        
        return User(id=user.id, name=user.name, email=user.email)
    
    @rpc(Integer, _returns=DeleteUserResponse)
    def DeleteUser(ctx, self, user_id):
        """Delete a user"""
        if not hasattr(self, 'users_db'):
            self.initialize_data()
        
        user = self.users_db.get(user_id)
        if not user:
            return DeleteUserResponse(
                success=False,
                message="User not found"
            )
        
        deleted_user = self.users_db.pop(user_id)
        return DeleteUserResponse(
            success=True,
            message=f"User {deleted_user.name} deleted successfully"
        )
    
    @rpc(Unicode, _returns=UserSearchResult)
    def SearchUsers(ctx, self, query):
        """Search users by name or email"""
        if not hasattr(self, 'users_db'):
            self.initialize_data()
        
        results = []
        query_lower = query.lower()
        
        for user in self.users_db.values():
            if (query_lower in user.name.lower() or 
                query_lower in user.email.lower()):
                results.append(User(id=user.id, name=user.name, email=user.email))
        
        return UserSearchResult(users=results)

# Initialize the service singleton
service_instance = UserService()

def create_app():
    """Create and configure the SOAP application"""
    application = Application(
        [UserService],
        tns='user_service.soap',
        in_protocol=Soap11(validator='lxml'),
        out_protocol=Soap11()
    )
    
    return application

def run_server():
    """Run the SOAP server"""
    application = create_app()
    wsgi_app = WsgiApplication(application)
    
    server = make_server('0.0.0.0', 8002, wsgi_app)
    
    print("SOAP Server started on http://localhost:8002")
    print(f"WSDL available at: http://localhost:8002?wsdl")
    print(f"Total users loaded: {len(service_instance.users_db)}")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down SOAP server...")

if __name__ == '__main__':
    run_server()