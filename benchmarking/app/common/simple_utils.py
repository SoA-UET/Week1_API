"""
Simple working benchmark implementation
"""
import csv
import time
import statistics
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import logging

@dataclass
class User:
    """User data model"""
    id: int
    name: str
    email: str
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email
        }

@dataclass
class BenchmarkResult:
    """Benchmark result data model"""
    api_type: str
    operation: str
    total_requests: int
    total_time: float
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    requests_per_second: float
    success_count: int
    error_count: int
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as a float between 0 and 1"""
        if self.total_requests == 0:
            return 0.0
        return self.success_count / self.total_requests

class DataLoader:
    """Utility class to load user data from CSV"""
    
    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)
        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    def load_users(self, limit: Optional[int] = None) -> List[User]:
        """Load users from CSV file"""
        users = []
        with open(self.csv_path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) >= 3:
                    try:
                        user_id = int(row[0])
                        name = row[1]
                        email = row[2]
                        users.append(User(id=user_id, name=name, email=email))
                        if limit and len(users) >= limit:
                            break
                    except (ValueError, IndexError):
                        continue
        return users

class SimpleBenchmarkRunner:
    """Simple benchmark runner without complex timing"""
    
    def __init__(self, name: str):
        self.name = name
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(name)
    
    def run_benchmark(self, operation: str, test_func, num_requests: int = 100) -> BenchmarkResult:
        """Run a simple benchmark test"""
        print(f"[{self.name}] Starting {operation} benchmark - {num_requests} requests")
        
        response_times = []
        success_count = 0
        error_count = 0
        
        start_time = time.perf_counter()
        
        for i in range(num_requests):
            try:
                request_start = time.perf_counter()
                result = test_func()
                request_end = time.perf_counter()
                
                response_times.append(request_end - request_start)
                
                if result:
                    success_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                error_count += 1
                if i < 5:  # Only log first few errors
                    print(f"Request {i+1} failed: {str(e)}")
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # Calculate metrics
        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
        else:
            avg_response_time = min_response_time = max_response_time = 0
        
        requests_per_second = num_requests / total_time if total_time > 0 else 0
        
        result = BenchmarkResult(
            api_type=self.name,
            operation=operation,
            total_requests=num_requests,
            total_time=total_time,
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            requests_per_second=requests_per_second,
            success_count=success_count,
            error_count=error_count
        )
        
        # Print results
        print(f"[{self.name}] {operation} Results:")
        print(f"  Total Requests: {num_requests}")
        print(f"  Success Rate: {(success_count/num_requests)*100:.1f}%")
        print(f"  Requests/sec: {requests_per_second:.2f}")
        print(f"  Avg Response Time: {avg_response_time*1000:.2f}ms")
        
        return result

class SimpleReportGenerator:
    """Generate simple comparison reports"""
    
    def generate_reports(self, results: List[BenchmarkResult]):
        """Generate and save both text and JSON reports"""
        # Generate text report
        text_report = self.generate_report(results)
        
        # Save text report
        with open('benchmark_report.txt', 'w', encoding='utf-8') as f:
            f.write(text_report)
        
        # Save JSON report
        self.export_to_json(results, 'benchmark_report.json')
    
    @staticmethod
    def generate_report(results: List[BenchmarkResult]) -> str:
        """Generate a simple comparison report"""
        if not results:
            return "No results to report"
        
        report_lines = [
            "=" * 80,
            "API PERFORMANCE BENCHMARK COMPARISON REPORT",
            "=" * 80,
            ""
        ]
        
        # Group by operation
        operations = {}
        for result in results:
            if result.operation not in operations:
                operations[result.operation] = []
            operations[result.operation].append(result)
        
        for operation, op_results in operations.items():
            report_lines.extend([
                f"Operation: {operation.upper()}",
                "-" * 50
            ])
            
            # Sort by requests per second
            op_results.sort(key=lambda x: x.requests_per_second, reverse=True)
            
            for i, result in enumerate(op_results, 1):
                status = "🏆" if i == 1 else f"{i}."
                report_lines.extend([
                    f"{status} {result.api_type.upper()}:",
                    f"    Requests/sec: {result.requests_per_second:.2f}",
                    f"    Avg Response: {result.avg_response_time*1000:.2f}ms",
                    f"    Success Rate: {(result.success_count/result.total_requests)*100:.1f}%",
                    ""
                ])
        
        return "\n".join(report_lines)
    
    @staticmethod
    def export_to_json(results: List[BenchmarkResult], output_file: str):
        """Export results to JSON"""
        data = []
        for result in results:
            data.append({
                'api_type': result.api_type,
                'operation': result.operation,
                'total_requests': result.total_requests,
                'total_time': result.total_time,
                'avg_response_time': result.avg_response_time,
                'min_response_time': result.min_response_time,
                'max_response_time': result.max_response_time,
                'requests_per_second': result.requests_per_second,
                'success_count': result.success_count,
                'error_count': result.error_count
            })
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

# For backward compatibility
BenchmarkRunner = SimpleBenchmarkRunner
ReportGenerator = SimpleReportGenerator

def get_csv_path() -> str:
    """Get the path to the users.csv file"""
    return str(Path(__file__).parent / "data" / "users.csv")