"""
Simple SOAP Server using Spyne
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from spyne import Application, rpc, ServiceBase, Integer, Unicode, ComplexModel, Array, Boolean
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
from wsgiref.simple_server import make_server
from common.simple_utils import DataLoader, User as UserModel

# SOAP Complex Models
class User(ComplexModel):
    id = Integer
    name = Unicode
    email = Unicode

class UserList(ComplexModel):
    users = Array(User)

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
        
        print(f"SOAP: Loaded {len(users)} users from CSV")
    except Exception as e:
        print(f"SOAP: Error loading data: {e}")

class UserService(ServiceBase):
    """SOAP User Service"""
    
    @rpc(Integer, Integer, _returns=UserList)
    def GetUsers(ctx, skip=0, limit=100):
        """Get all users with pagination"""
        user_list = list(users_db.values())[skip:skip + limit]
        
        users = []
        for user in user_list:
            users.append(User(id=user.id, name=user.name, email=user.email))
        
        return UserList(users=users)
    
    @rpc(Integer, _returns=User)
    def GetUser(ctx, user_id):
        """Get user by ID"""
        user = users_db.get(user_id)
        if user:
            return User(id=user.id, name=user.name, email=user.email)
        return None
    
    @rpc(Unicode, Unicode, _returns=User)
    def CreateUser(ctx, name, email):
        """Create a new user"""
        global next_id
        user = UserModel(id=next_id, name=name, email=email)
        users_db[next_id] = user
        next_id += 1
        
        return User(id=user.id, name=user.name, email=user.email)

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
    initialize_data()
    
    application = create_app()
    wsgi_app = WsgiApplication(application)
    
    server = make_server('127.0.0.1', 8002, wsgi_app)
    
    print("SOAP Server started on http://localhost:8002")
    print(f"WSDL available at: http://localhost:8002?wsdl")
    print(f"Total users loaded: {len(users_db)}")
    
    return server

if __name__ == '__main__':
    server = run_server()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down SOAP server...")