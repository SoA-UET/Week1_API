"""
Simple GraphQL Client and Benchmark using modern libraries
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import requests
import json
import random
import uuid
from typing import List, Dict
from common.simple_utils import SimpleBenchmarkRunner, BenchmarkResult, DataLoader, User

class SimpleGraphQLClient:
    """Simple GraphQL client using requests"""
    
    def __init__(self, endpoint: str = "http://localhost:8001/graphql"):
        self.endpoint = endpoint
        self.session = requests.Session()
        self.session.timeout = 10
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def execute_query(self, query: str, variables: dict = None) -> dict:
        """Execute GraphQL query"""
        payload = {
            "query": query,
            "variables": variables or {}
        }
        
        response = self.session.post(self.endpoint, 
                                   data=json.dumps(payload))
        response.raise_for_status()
        
        result = response.json()
        if "errors" in result:
            raise Exception(f"GraphQL Error: {result['errors']}")
        
        return result["data"]
    
    def get_users(self, limit: int = 20) -> List[dict]:
        """Get all users via GraphQL"""
        query = """
        query GetUsers($limit: Int) {
            users(limit: $limit) {
                id
                name
                email
            }
        }
        """
        data = self.execute_query(query, {"limit": limit})
        return data["users"]
    
    def get_user(self, user_id: int) -> dict:
        """Get user by ID via GraphQL"""
        query = """
        query GetUser($id: Int!) {
            user(id: $id) {
                id
                name
                email
            }
        }
        """
        data = self.execute_query(query, {"id": user_id})
        return data["user"]
    
    def create_user(self, name: str, email: str) -> dict:
        """Create user via GraphQL"""
        mutation = """
        mutation CreateUser($name: String!, $email: String!) {
            createUser(name: $name, email: $email) {
                id
                name
                email
            }
        }
        """
        data = self.execute_query(mutation, {"name": name, "email": email})
        return data["createUser"]

class SimpleGraphQLBenchmark(SimpleBenchmarkRunner):
    """Simple GraphQL benchmark runner"""
    
    def __init__(self, endpoint: str = "http://localhost:8001/graphql"):
        super().__init__("GraphQL")
        self.client = SimpleGraphQLClient(endpoint)
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
        """Run all GraphQL benchmarks"""
        results = []
        
        print(f"Starting GraphQL benchmarks with {num_requests} requests each...")
        
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
GraphQLBenchmark = SimpleGraphQLBenchmark

if __name__ == "__main__":
    benchmark = SimpleGraphQLBenchmark()
    results = benchmark.run_all_benchmarks(30)
    print(f"\nGraphQL Benchmark completed with {len(results)} results")