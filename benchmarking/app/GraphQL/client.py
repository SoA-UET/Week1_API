"""
GraphQL Client and Benchmark Implementation
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

class GraphQLClient:
    """GraphQL API client"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = f"{base_url}/graphql"
        self.session = requests.Session()
    
    def _execute_query(self, query: str, variables: dict = None) -> dict:
        """Execute a GraphQL query"""
        payload = {
            "query": query,
            "variables": variables or {}
        }
        
        response = self.session.post(self.base_url, json=payload)
        response.raise_for_status()
        
        result = response.json()
        if "errors" in result:
            raise Exception(f"GraphQL errors: {result['errors']}")
        
        return result["data"]
    
    def get_users(self, skip: int = 0, limit: int = 100) -> List[dict]:
        """Get all users"""
        query = """
        query GetUsers($skip: Int, $limit: Int) {
            users(skip: $skip, limit: $limit) {
                id
                name
                email
            }
        }
        """
        
        data = self._execute_query(query, {"skip": skip, "limit": limit})
        return data["users"]
    
    def get_user(self, user_id: int) -> dict:
        """Get user by ID"""
        query = """
        query GetUser($userId: Int!) {
            user(userId: $userId) {
                id
                name
                email
            }
        }
        """
        
        data = self._execute_query(query, {"userId": user_id})
        return data["user"]
    
    def create_user(self, name: str, email: str) -> dict:
        """Create a new user"""
        mutation = """
        mutation CreateUser($userData: UserInput!) {
            createUser(userData: $userData) {
                user {
                    id
                    name
                    email
                }
                success
            }
        }
        """
        
        variables = {
            "userData": {
                "name": name,
                "email": email
            }
        }
        
        data = self._execute_query(mutation, variables)
        return data["createUser"]
    
    def update_user(self, user_id: int, name: str = None, email: str = None) -> dict:
        """Update an existing user"""
        mutation = """
        mutation UpdateUser($userId: Int!, $userData: UserUpdateInput!) {
            updateUser(userId: $userId, userData: $userData) {
                user {
                    id
                    name
                    email
                }
                success
            }
        }
        """
        
        user_data = {}
        if name:
            user_data["name"] = name
        if email:
            user_data["email"] = email
        
        variables = {
            "userId": user_id,
            "userData": user_data
        }
        
        data = self._execute_query(mutation, variables)
        return data["updateUser"]
    
    def delete_user(self, user_id: int) -> dict:
        """Delete a user"""
        mutation = """
        mutation DeleteUser($userId: Int!) {
            deleteUser(userId: $userId) {
                success
                message
            }
        }
        """
        
        data = self._execute_query(mutation, {"userId": user_id})
        return data["deleteUser"]
    
    def search_users(self, query: str) -> List[dict]:
        """Search users"""
        graphql_query = """
        query SearchUsers($query: String!) {
            searchUsers(query: $query) {
                id
                name
                email
            }
        }
        """
        
        data = self._execute_query(graphql_query, {"query": query})
        return data["searchUsers"]

class GraphQLBenchmark(BenchmarkRunner):
    """GraphQL API benchmark runner"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        super().__init__("GraphQL")
        self.client = GraphQLClient(base_url)
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
        """Run all GraphQL API benchmarks"""
        results = []
        
        self.logger.info("Starting GraphQL API benchmarks...")
        
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
    # Test the GraphQL client
    benchmark = GraphQLBenchmark()
    results = benchmark.run_all_benchmarks(50)
    
    print(f"\nGraphQL API Benchmark completed with {len(results)} results")
    for result in results:
        print(f"- {result.operation}: {result.requests_per_second:.2f} req/sec")