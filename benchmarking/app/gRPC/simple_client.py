"""
Simple gRPC Client and Benchmark
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import grpc
import random
import uuid
from typing import List, Dict
from common.simple_utils import SimpleBenchmarkRunner, BenchmarkResult, DataLoader, User

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

class SimplegRPCClient:
    """Simple gRPC client"""
    
    def __init__(self, server_address: str = "localhost:50051"):
        if not GRPC_AVAILABLE:
            raise ImportError("gRPC protobuf files not available")
        
        self.server_address = server_address
        self.channel = None
        self.stub = None
    
    def connect(self):
        """Connect to gRPC server"""
        try:
            self.channel = grpc.insecure_channel(self.server_address)
            self.stub = user_service_pb2_grpc.UserServiceStub(self.channel)
            return True
        except Exception as e:
            print(f"Failed to connect to gRPC server: {e}")
            return False
    
    def get_users(self, skip: int = 0, limit: int = 20) -> List[dict]:
        """Get all users"""
        if not self.stub and not self.connect():
            raise Exception("gRPC service not available")
        
        request = user_service_pb2.GetUsersRequest(skip=skip, limit=limit)
        response = self.stub.GetUsers(request)
        
        return [
            {"id": user.id, "name": user.name, "email": user.email}
            for user in response.users
        ]
    
    def get_user(self, user_id: int) -> dict:
        """Get user by ID"""
        if not self.stub and not self.connect():
            raise Exception("gRPC service not available")
        
        request = user_service_pb2.GetUserRequest(user_id=user_id)
        response = self.stub.GetUser(request)
        
        if response.found:
            user = response.user
            return {"id": user.id, "name": user.name, "email": user.email}
        return None
    
    def create_user(self, name: str, email: str) -> dict:
        """Create a new user"""
        if not self.stub and not self.connect():
            raise Exception("gRPC service not available")
        
        request = user_service_pb2.CreateUserRequest(name=name, email=email)
        response = self.stub.CreateUser(request)
        
        if response.success:
            user = response.user
            return {"id": user.id, "name": user.name, "email": user.email}
        return None
    
    def close(self):
        """Close connection"""
        if self.channel:
            self.channel.close()

class SimplegRPCBenchmark(SimpleBenchmarkRunner):
    """Simple gRPC benchmark runner"""
    
    def __init__(self, server_address: str = "localhost:50051"):
        super().__init__("gRPC")
        
        if not GRPC_AVAILABLE:
            print("gRPC protobuf files not available - skipping gRPC benchmarks")
            self.client = None
            return
        
        self.client = SimplegRPCClient(server_address)
        self.test_users = []
        
        # Load test data
        try:
            csv_path = Path(__file__).parent.parent / "common" / "data" / "users.csv"
            loader = DataLoader(str(csv_path))
            self.test_users = loader.load_users(50)
            print(f"Loaded {len(self.test_users)} test users")
        except Exception as e:
            print(f"Failed to load test data: {e}")
    
    def benchmark_get_all_users(self, num_requests: int = 30) -> BenchmarkResult:
        """Benchmark getting all users"""
        if not self.client:
            return None
            
        def test_func():
            try:
                result = self.client.get_users(limit=10)
                return len(result) > 0
            except Exception:
                return False
        
        return self.run_benchmark("get_all_users", test_func, num_requests)
    
    def benchmark_get_user_by_id(self, num_requests: int = 30) -> BenchmarkResult:
        """Benchmark getting user by ID"""
        if not self.client or not self.test_users:
            return None
        
        def test_func():
            try:
                user = random.choice(self.test_users)
                result = self.client.get_user(user.id)
                return result and result.get("id") == user.id
            except Exception:
                return False
        
        return self.run_benchmark("get_user_by_id", test_func, num_requests)
    
    def benchmark_create_user(self, num_requests: int = 20) -> BenchmarkResult:
        """Benchmark creating users"""
        if not self.client:
            return None
            
        def test_func():
            try:
                unique_id = str(uuid.uuid4())[:8]
                name = f"Test User {unique_id}"
                email = f"test.{unique_id}@benchmark.com"
                
                result = self.client.create_user(name, email)
                return result and result.get("id") is not None
            except Exception:
                return False
        
        return self.run_benchmark("create_user", test_func, num_requests)
    
    def run_all_benchmarks(self, num_requests: int = 30) -> List[BenchmarkResult]:
        """Run all gRPC benchmarks"""
        results = []
        
        if not self.client:
            print("gRPC client not available - skipping benchmarks")
            return results
        
        print(f"Starting gRPC benchmarks with {num_requests} requests each...")
        
        benchmarks = [
            ("Get All Users", lambda: self.benchmark_get_all_users(num_requests)),
            ("Get User By ID", lambda: self.benchmark_get_user_by_id(num_requests)),
            ("Create User", lambda: self.benchmark_create_user(min(20, num_requests)))
        ]
        
        for name, benchmark_func in benchmarks:
            try:
                print(f"\nRunning {name} benchmark...")
                result = benchmark_func()
                if result:
                    results.append(result)
            except Exception as e:
                print(f"Failed to run {name} benchmark: {e}")
        
        return results
    
    def cleanup(self):
        """Clean up resources"""
        if self.client:
            self.client.close()

# For backward compatibility  
gRPCBenchmark = SimplegRPCBenchmark

if __name__ == "__main__":
    benchmark = SimplegRPCBenchmark()
    try:
        results = benchmark.run_all_benchmarks(30)
        print(f"\ngRPC Benchmark completed with {len(results)} results")
    finally:
        benchmark.cleanup()