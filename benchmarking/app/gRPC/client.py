"""
gRPC Client and Benchmark Implementation
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import grpc
import random
from typing import List, Dict, Any

# Import generated protobuf files - only import if they exist
user_service_pb2 = None
user_service_pb2_grpc = None

try:
    import user_service_pb2
    import user_service_pb2_grpc
    GRPC_PROTO_AVAILABLE = True
except ImportError:
    GRPC_PROTO_AVAILABLE = False
    print("Warning: gRPC protobuf files not found. Generate them with:")
    print("cd app/gRPC && python -m grpc_tools.protoc --proto_path=proto --python_out=. --grpc_python_out=. proto/user_service.proto")

from common.utils import BenchmarkRunner, BenchmarkResult, DataLoader
from common.models import User

class gRPCClient:
    """gRPC API client"""
    
    def __init__(self, server_address: str = "localhost:50051"):
        if not GRPC_PROTO_AVAILABLE:
            raise ImportError("gRPC protobuf files not available")
        
        self.server_address = server_address
        self.channel = grpc.insecure_channel(server_address)
        self.stub = user_service_pb2_grpc.UserServiceStub(self.channel)
    
    def get_users(self, skip: int = 0, limit: int = 100) -> List[dict]:
        """Get all users"""
        request = user_service_pb2.GetUsersRequest(skip=skip, limit=limit)
        response = self.stub.GetUsers(request)
        
        return [
            {"id": user.id, "name": user.name, "email": user.email}
            for user in response.users
        ]
    
    def get_user(self, user_id: int) -> dict:
        """Get user by ID"""
        request = user_service_pb2.GetUserRequest(user_id=user_id)
        response = self.stub.GetUser(request)
        
        if response.found:
            user = response.user
            return {"id": user.id, "name": user.name, "email": user.email}
        return None
    
    def create_user(self, name: str, email: str) -> dict:
        """Create a new user"""
        request = user_service_pb2.CreateUserRequest(name=name, email=email)
        response = self.stub.CreateUser(request)
        
        if response.success:
            user = response.user
            return {
                "success": True,
                "user": {"id": user.id, "name": user.name, "email": user.email}
            }
        return {"success": False}
    
    def update_user(self, user_id: int, name: str = None, email: str = None) -> dict:
        """Update an existing user"""
        request = user_service_pb2.UpdateUserRequest(
            user_id=user_id,
            name=name or "",
            email=email or ""
        )
        response = self.stub.UpdateUser(request)
        
        if response.success:
            user = response.user
            return {
                "success": True,
                "user": {"id": user.id, "name": user.name, "email": user.email}
            }
        return {"success": False}
    
    def delete_user(self, user_id: int) -> dict:
        """Delete a user"""
        request = user_service_pb2.DeleteUserRequest(user_id=user_id)
        response = self.stub.DeleteUser(request)
        
        return {
            "success": response.success,
            "message": response.message
        }
    
    def search_users(self, query: str) -> List[dict]:
        """Search users"""
        request = user_service_pb2.SearchUsersRequest(query=query)
        response = self.stub.SearchUsers(request)
        
        return [
            {"id": user.id, "name": user.name, "email": user.email}
            for user in response.users
        ]
    
    def close(self):
        """Close the gRPC channel"""
        self.channel.close()

class gRPCBenchmark(BenchmarkRunner):
    """gRPC API benchmark runner"""
    
    def __init__(self, server_address: str = "localhost:50051"):
        super().__init__("gRPC")
        
        if not GRPC_PROTO_AVAILABLE:
            raise ImportError("gRPC protobuf files not available. Please generate them first.")
        
        self.client = gRPCClient(server_address)
        self.test_users = []
        self.created_user_ids = []
        
        # Load test data
        try:
            csv_path = Path(__file__).parent.parent / "common" / "data" / "users.csv"
            loader = DataLoader(str(csv_path))
            self.test_users = loader.load_users(50)  # Use first 50 for testing
        except Exception as e:
            self.logger.error(f"Failed to load test data: {e}")
    
    def benchmark_get_all_users(self, num_requests: int = 100) -> BenchmarkResult:
        """Benchmark getting all users"""
        def test_func():
            try:
                result = self.client.get_users(limit=20)  # Limit for faster response
                return len(result) > 0
            except Exception:
                return False
        
        return self.run_benchmark("get_all_users", test_func, num_requests)
    
    def benchmark_get_user_by_id(self, num_requests: int = 100) -> BenchmarkResult:
        """Benchmark getting user by ID"""
        if not self.test_users:
            self.logger.error("No test users available")
            return None
        
        def test_func():
            try:
                # Random user ID from test data
                user = random.choice(self.test_users)
                result = self.client.get_user(user.id)
                return result and result.get("id") == user.id
            except Exception:
                return False
        
        return self.run_benchmark("get_user_by_id", test_func, num_requests)
    
    def benchmark_create_user(self, num_requests: int = 50) -> BenchmarkResult:
        """Benchmark creating users"""
        def test_func():
            try:
                # Generate unique user data
                import uuid
                unique_id = str(uuid.uuid4())[:8]
                name = f"Test User {unique_id}"
                email = f"test.{unique_id}@benchmark.com"
                
                result = self.client.create_user(name, email)
                if result.get("success") and result.get("user", {}).get("id"):
                    self.created_user_ids.append(result["user"]["id"])
                    return True
                return False
            except Exception:
                return False
        
        return self.run_benchmark("create_user", test_func, num_requests)
    
    def benchmark_update_user(self, num_requests: int = 50) -> BenchmarkResult:
        """Benchmark updating users"""
        if not self.test_users:
            self.logger.error("No test users available")
            return None
        
        def test_func():
            try:
                # Use random existing user
                user = random.choice(self.test_users)
                new_name = f"Updated {user.name}"
                result = self.client.update_user(user.id, name=new_name)
                return result.get("success") and result.get("user", {}).get("name") == new_name
            except Exception:
                return False
        
        return self.run_benchmark("update_user", test_func, num_requests)
    
    def benchmark_delete_user(self, num_requests: int = 30) -> BenchmarkResult:
        """Benchmark deleting users"""
        # Only delete users we created during benchmarking
        if not self.created_user_ids:
            self.logger.warning("No created users available for deletion test")
            # Create some users first
            self.benchmark_create_user(num_requests)
        
        def test_func():
            try:
                if self.created_user_ids:
                    user_id = self.created_user_ids.pop()
                    result = self.client.delete_user(user_id)
                    return result.get("success") == True
                return False
            except Exception:
                return False
        
        return self.run_benchmark("delete_user", test_func, 
                                min(num_requests, len(self.created_user_ids)))
    
    def benchmark_search_users(self, num_requests: int = 100) -> BenchmarkResult:
        """Benchmark searching users"""
        search_terms = ["Nguyễn", "Trần", "Phạm", "Lê", "Hoàng", "Vũ", "Đỗ", "gmail"]
        
        def test_func():
            try:
                query = random.choice(search_terms)
                result = self.client.search_users(query)
                return isinstance(result, list)
            except Exception:
                return False
        
        return self.run_benchmark("search_users", test_func, num_requests)
    
    def run_all_benchmarks(self, num_requests: int = 100) -> List[BenchmarkResult]:
        """Run all gRPC API benchmarks"""
        results = []
        
        self.logger.info("Starting gRPC API benchmarks...")
        
        # Run benchmarks in order
        benchmarks = [
            ("Get All Users", lambda: self.benchmark_get_all_users(num_requests)),
            ("Get User By ID", lambda: self.benchmark_get_user_by_id(num_requests)),
            ("Create User", lambda: self.benchmark_create_user(max(30, num_requests//2))),
            ("Update User", lambda: self.benchmark_update_user(max(30, num_requests//2))),
            ("Search Users", lambda: self.benchmark_search_users(num_requests)),
            ("Delete User", lambda: self.benchmark_delete_user(max(20, num_requests//3)))
        ]
        
        for name, benchmark_func in benchmarks:
            try:
                self.logger.info(f"Running {name} benchmark...")
                result = benchmark_func()
                if result:
                    results.append(result)
            except Exception as e:
                self.logger.error(f"Failed to run {name} benchmark: {e}")
        
        return results
    
    def cleanup(self):
        """Clean up resources"""
        self.client.close()

if __name__ == "__main__":
    # Test the gRPC client
    benchmark = gRPCBenchmark()
    try:
        results = benchmark.run_all_benchmarks(50)
        
        print(f"\ngRPC API Benchmark completed with {len(results)} results")
        for result in results:
            print(f"- {result.operation}: {result.requests_per_second:.2f} req/sec")
    finally:
        benchmark.cleanup()