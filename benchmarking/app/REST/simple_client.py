"""
Simple working REST API Client and Benchmark
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import requests
import random
import uuid
from typing import List, Dict
from common.simple_utils import SimpleBenchmarkRunner, BenchmarkResult, DataLoader, User

class SimpleRESTClient:
    """Simple REST API client"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 10  # 10 second timeout
    
    def get_users(self, limit: int = 20) -> List[dict]:
        """Get all users"""
        response = self.session.get(f"{self.base_url}/users", 
                                   params={"limit": limit})
        response.raise_for_status()
        return response.json()
    
    def get_user(self, user_id: int) -> dict:
        """Get user by ID"""
        response = self.session.get(f"{self.base_url}/users/{user_id}")
        response.raise_for_status()
        return response.json()
    
    def create_user(self, name: str, email: str) -> dict:
        """Create a new user"""
        data = {"name": name, "email": email}
        response = self.session.post(f"{self.base_url}/users", json=data)
        response.raise_for_status()
        return response.json()

class SimpleRESTBenchmark(SimpleBenchmarkRunner):
    """Simple REST API benchmark runner"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        super().__init__("REST")
        self.client = SimpleRESTClient(base_url)
        self.test_users = []
        
        # Load test data
        try:
            csv_path = Path(__file__).parent.parent / "common" / "data" / "users.csv"
            loader = DataLoader(str(csv_path))
            self.test_users = loader.load_users(50)
            print(f"Loaded {len(self.test_users)} test users")
        except Exception as e:
            print(f"Failed to load test data: {e}")
    
    def benchmark_get_all_users(self, num_requests: int = 50) -> BenchmarkResult:
        """Benchmark getting all users"""
        def test_func():
            try:
                result = self.client.get_users(limit=10)
                return len(result) > 0
            except Exception:
                return False
        
        return self.run_benchmark("get_all_users", test_func, num_requests)
    
    def benchmark_get_user_by_id(self, num_requests: int = 50) -> BenchmarkResult:
        """Benchmark getting user by ID"""
        if not self.test_users:
            print("No test users available")
            return None
        
        def test_func():
            try:
                user = random.choice(self.test_users)
                result = self.client.get_user(user.id)
                return result.get("id") == user.id
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
    
    def run_all_benchmarks(self, num_requests: int = 50) -> List[BenchmarkResult]:
        """Run all REST API benchmarks"""
        results = []
        
        print(f"Starting REST API benchmarks with {num_requests} requests each...")
        
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
RESTBenchmark = SimpleRESTBenchmark

if __name__ == "__main__":
    benchmark = SimpleRESTBenchmark()
    results = benchmark.run_all_benchmarks(30)
    print(f"\nREST API Benchmark completed with {len(results)} results")