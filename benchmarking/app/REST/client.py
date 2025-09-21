"""
REST API Client and Benchmark Implementation
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import requests
import json
import random
from typing import List, Dict, Any
from common.utils import BenchmarkRunner, BenchmarkResult, DataLoader
from common.models import User

class RESTClient:
    """REST API client"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def get_users(self, skip: int = 0, limit: int = 100) -> List[dict]:
        """Get all users"""
        response = self.session.get(f"{self.base_url}/users", 
                                   params={"skip": skip, "limit": limit})
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
    
    def update_user(self, user_id: int, name: str = None, email: str = None) -> dict:
        """Update an existing user"""
        data = {}
        if name:
            data["name"] = name
        if email:
            data["email"] = email
        
        response = self.session.put(f"{self.base_url}/users/{user_id}", json=data)
        response.raise_for_status()
        return response.json()
    
    def delete_user(self, user_id: int) -> dict:
        """Delete a user"""
        response = self.session.delete(f"{self.base_url}/users/{user_id}")
        response.raise_for_status()
        return response.json()
    
    def search_users(self, query: str) -> List[dict]:
        """Search users"""
        response = self.session.get(f"{self.base_url}/users/search/{query}")
        response.raise_for_status()
        return response.json()

class RESTBenchmark(BenchmarkRunner):
    """REST API benchmark runner"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        super().__init__("REST")
        self.client = RESTClient(base_url)
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
                return result.get("id") == user.id
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
                if result.get("id"):
                    self.created_user_ids.append(result["id"])
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
                return result.get("name") == new_name
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
                    return "deleted successfully" in result.get("message", "")
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
        """Run all REST API benchmarks"""
        results = []
        
        self.logger.info("Starting REST API benchmarks...")
        
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
    # Test the REST client
    benchmark = RESTBenchmark()
    results = benchmark.run_all_benchmarks(50)
    
    print(f"\nREST API Benchmark completed with {len(results)} results")
    for result in results:
        print(f"- {result.operation}: {result.requests_per_second:.2f} req/sec")