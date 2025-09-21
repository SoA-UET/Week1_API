"""
Simple SOAP Client and Benchmark using modern libraries
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from zeep import Client
from zeep.exceptions import Fault
import random
import uuid
from typing import List, Dict
from common.simple_utils import SimpleBenchmarkRunner, BenchmarkResult, DataLoader, User

class SimpleSOAPClient:
    """Simple SOAP API client using Zeep"""
    
    def __init__(self, wsdl_url: str = "http://localhost:8002?wsdl"):
        self.wsdl_url = wsdl_url
        self.client = None
        self.service = None
        
    def connect(self):
        """Connect to SOAP service"""
        try:
            self.client = Client(self.wsdl_url)
            self.service = self.client.service
            return True
        except Exception as e:
            print(f"Failed to connect to SOAP service: {e}")
            return False
    
    def get_users(self, skip: int = 0, limit: int = 20) -> List[dict]:
        """Get all users"""
        if not self.service and not self.connect():
            raise Exception("SOAP service not available")
        
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
        except Exception as e:
            raise Exception(f"SOAP error: {e}")
    
    def get_user(self, user_id: int) -> dict:
        """Get user by ID"""
        if not self.service and not self.connect():
            raise Exception("SOAP service not available")
        
        try:
            user = self.service.GetUser(user_id=user_id)
            
            if user:
                return {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email
                }
            return None
        except Exception as e:
            raise Exception(f"SOAP error: {e}")
    
    def create_user(self, name: str, email: str) -> dict:
        """Create a new user"""
        if not self.service and not self.connect():
            raise Exception("SOAP service not available")
        
        try:
            user = self.service.CreateUser(name=name, email=email)
            
            return {
                "id": user.id,
                "name": user.name,
                "email": user.email
            }
        except Exception as e:
            raise Exception(f"SOAP error: {e}")

class SimpleSOAPBenchmark(SimpleBenchmarkRunner):
    """Simple SOAP benchmark runner"""
    
    def __init__(self, wsdl_url: str = "http://localhost:8002?wsdl"):
        super().__init__("SOAP")
        self.client = SimpleSOAPClient(wsdl_url)
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
        def test_func():
            try:
                result = self.client.get_users(limit=10)
                # Check if we got a valid list of users
                return isinstance(result, list) and len(result) >= 0
            except Exception as e:
                print(f"SOAP get_users error: {e}")
                return False
        
        return self.run_benchmark("get_all_users", test_func, num_requests)
    
    def benchmark_get_user_by_id(self, num_requests: int = 30) -> BenchmarkResult:
        """Benchmark getting user by ID"""
        if not self.test_users:
            print("No test users available")
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
        def test_func():
            try:
                unique_id = str(uuid.uuid4())[:8]
                name = f"Test User {unique_id}"
                email = f"test.{unique_id}@benchmark.com"
                
                result = self.client.create_user(name, email)
                return result.get("id") is not None
            except Exception:
                return False
        
        return self.run_benchmark("create_user", test_func, num_requests)
    
    def run_all_benchmarks(self, num_requests: int = 30) -> List[BenchmarkResult]:
        """Run all SOAP benchmarks"""
        results = []
        
        print(f"Starting SOAP benchmarks with {num_requests} requests each...")
        
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

# For backward compatibility
SOAPBenchmark = SimpleSOAPBenchmark

if __name__ == "__main__":
    benchmark = SimpleSOAPBenchmark()
    results = benchmark.run_all_benchmarks(30)
    print(f"\nSOAP Benchmark completed with {len(results)} results")