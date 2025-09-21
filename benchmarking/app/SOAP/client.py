"""
SOAP Client and Benchmark Implementation
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from zeep import Client
from zeep.exceptions import Fault
import random
from typing import List, Dict, Any
from common.utils import BenchmarkRunner, BenchmarkResult, DataLoader
from common.models import User

class SOAPClient:
    """SOAP API client"""
    
    def __init__(self, wsdl_url: str = "http://localhost:8002?wsdl"):
        self.wsdl_url = wsdl_url
        try:
            self.client = Client(wsdl_url)
            self.service = self.client.service
        except Exception as e:
            print(f"Failed to initialize SOAP client: {e}")
            self.client = None
            self.service = None
    
    def get_users(self, skip: int = 0, limit: int = 100) -> List[dict]:
        """Get all users"""
        if not self.service:
            raise Exception("SOAP client not initialized")
        
        try:
            response = self.service.GetUsers(skip=skip, limit=limit)
            users = []
            
            if hasattr(response, 'users') and response.users:
                for user in response.users:
                    users.append({
                        "id": user.id,
                        "name": user.name,
                        "email": user.email
                    })
            
            return users
        except Fault as fault:
            raise Exception(f"SOAP fault: {fault}")
    
    def get_user(self, user_id: int) -> dict:
        """Get user by ID"""
        if not self.service:
            raise Exception("SOAP client not initialized")
        
        try:
            user = self.service.GetUser(user_id=user_id)
            
            if user:
                return {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email
                }
            return None
        except Fault as fault:
            raise Exception(f"SOAP fault: {fault}")
    
    def create_user(self, name: str, email: str) -> dict:
        """Create a new user"""
        if not self.service:
            raise Exception("SOAP client not initialized")
        
        try:
            user = self.service.CreateUser(name=name, email=email)
            
            return {
                "success": True,
                "user": {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email
                }
            }
        except Fault as fault:
            raise Exception(f"SOAP fault: {fault}")
    
    def update_user(self, user_id: int, name: str = None, email: str = None) -> dict:
        """Update an existing user"""
        if not self.service:
            raise Exception("SOAP client not initialized")
        
        try:
            user = self.service.UpdateUser(
                user_id=user_id,
                name=name,
                email=email
            )
            
            if user:
                return {
                    "success": True,
                    "user": {
                        "id": user.id,
                        "name": user.name,
                        "email": user.email
                    }
                }
            return {"success": False}
        except Fault as fault:
            raise Exception(f"SOAP fault: {fault}")
    
    def delete_user(self, user_id: int) -> dict:
        """Delete a user"""
        if not self.service:
            raise Exception("SOAP client not initialized")
        
        try:
            response = self.service.DeleteUser(user_id=user_id)
            
            return {
                "success": response.success,
                "message": response.message
            }
        except Fault as fault:
            raise Exception(f"SOAP fault: {fault}")
    
    def search_users(self, query: str) -> List[dict]:
        """Search users"""
        if not self.service:
            raise Exception("SOAP client not initialized")
        
        try:
            response = self.service.SearchUsers(query=query)
            users = []
            
            if hasattr(response, 'users') and response.users:
                for user in response.users:
                    users.append({
                        "id": user.id,
                        "name": user.name,
                        "email": user.email
                    })
            
            return users
        except Fault as fault:
            raise Exception(f"SOAP fault: {fault}")

class SOAPBenchmark(BenchmarkRunner):
    """SOAP API benchmark runner"""
    
    def __init__(self, wsdl_url: str = "http://localhost:8002?wsdl"):
        super().__init__("SOAP")
        self.client = SOAPClient(wsdl_url)
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
        """Run all SOAP API benchmarks"""
        results = []
        
        self.logger.info("Starting SOAP API benchmarks...")
        
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

if __name__ == "__main__":
    # Test the SOAP client
    benchmark = SOAPBenchmark()
    results = benchmark.run_all_benchmarks(50)
    
    print(f"\nSOAP API Benchmark completed with {len(results)} results")
    for result in results:
        print(f"- {result.operation}: {result.requests_per_second:.2f} req/sec")