import csv
import time
import statistics
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import logging

# Simple color codes without colorama dependency
class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    WHITE = '\033[97m'
    RED = '\033[91m'
    RESET = '\033[0m'

@dataclass
class User:
    """User data model"""
    id: int
    name: str
    email: str

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
    error_rate: float

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

class BenchmarkTimer:
    """Utility class for timing operations"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.response_times = []
    
    def start(self):
        """Start timing"""
        self.start_time = time.perf_counter()
    
    def stop(self):
        """Stop timing"""
        self.end_time = time.perf_counter()
        if self.start_time:
            response_time = self.end_time - self.start_time
            self.response_times.append(response_time)
            return response_time
        return 0
    
    def get_total_time(self) -> float:
        """Get total elapsed time"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0
    
    def get_statistics(self) -> Dict[str, float]:
        """Get timing statistics"""
        if not self.response_times:
            return {
                'avg': 0, 'min': 0, 'max': 0,
                'median': 0, 'std_dev': 0
            }
        
        return {
            'avg': statistics.mean(self.response_times),
            'min': min(self.response_times),
            'max': max(self.response_times),
            'median': statistics.median(self.response_times),
            'std_dev': statistics.stdev(self.response_times) if len(self.response_times) > 1 else 0
        }

class BenchmarkRunner:
    """Base class for running benchmarks on different API types"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Set up logger for the benchmark"""
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f'{Colors.CYAN}[%(name)s]{Colors.RESET} %(levelname)s: %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def run_benchmark(self, operation: str, test_func, num_requests: int = 100, 
                     concurrent: bool = False) -> BenchmarkResult:
        """Run a benchmark test"""
        self.logger.info(f"Starting {operation} benchmark - {num_requests} requests")
        
        timer = BenchmarkTimer()
        success_count = 0
        error_count = 0
        
        timer.start()
        
        if concurrent:
            # TODO: Implement concurrent execution
            pass
        
        # Sequential execution
        for i in range(num_requests):
            try:
                individual_timer = BenchmarkTimer()
                individual_timer.start()
                
                result = test_func()
                
                individual_timer.stop()
                timer.response_times.extend(individual_timer.response_times)
                
                if result:
                    success_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                error_count += 1
                self.logger.error(f"Request {i+1} failed: {str(e)}")
        
        timer.stop()
        
        # Calculate metrics
        total_time = timer.get_total_time()
        stats = timer.get_statistics()
        
        result = BenchmarkResult(
            api_type=self.name,
            operation=operation,
            total_requests=num_requests,
            total_time=total_time,
            avg_response_time=stats['avg'],
            min_response_time=stats['min'],
            max_response_time=stats['max'],
            requests_per_second=num_requests / total_time if total_time > 0 else 0,
            success_count=success_count,
            error_count=error_count,
            error_rate=(error_count / num_requests) * 100
        )
        
        self._log_results(result)
        return result
    
    def _log_results(self, result: BenchmarkResult):
        """Log benchmark results"""
        self.logger.info(f"{Fore.GREEN}Benchmark Results:{Style.RESET_ALL}")
        self.logger.info(f"  Operation: {result.operation}")
        self.logger.info(f"  Total Requests: {result.total_requests}")
        self.logger.info(f"  Success Rate: {Fore.GREEN}{(result.success_count/result.total_requests)*100:.1f}%{Style.RESET_ALL}")
        self.logger.info(f"  Requests/sec: {Fore.YELLOW}{result.requests_per_second:.2f}{Style.RESET_ALL}")
        self.logger.info(f"  Avg Response Time: {result.avg_response_time*1000:.2f}ms")
        self.logger.info(f"  Min/Max Response Time: {result.min_response_time*1000:.2f}ms / {result.max_response_time*1000:.2f}ms")

class ReportGenerator:
    """Generate comparison reports for benchmark results"""
    
    @staticmethod
    def generate_comparison_report(results: List[BenchmarkResult], 
                                 output_file: Optional[str] = None) -> str:
        """Generate a comparison report of all benchmark results"""
        report_lines = [
            f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}",
            f"{Fore.CYAN}API PERFORMANCE BENCHMARK COMPARISON REPORT{Style.RESET_ALL}",
            f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}",
            ""
        ]
        
        # Group results by operation
        operations = {}
        for result in results:
            if result.operation not in operations:
                operations[result.operation] = []
            operations[result.operation].append(result)
        
        # Generate report for each operation
        for operation, op_results in operations.items():
            report_lines.extend([
                f"{Fore.YELLOW}Operation: {operation.upper()}{Style.RESET_ALL}",
                f"{'-' * 50}"
            ])
            
            # Sort by requests per second (performance)
            op_results.sort(key=lambda x: x.requests_per_second, reverse=True)
            
            for i, result in enumerate(op_results, 1):
                status = f"{Fore.GREEN}🏆{Style.RESET_ALL}" if i == 1 else f"{Fore.WHITE}{i}.{Style.RESET_ALL}"
                report_lines.extend([
                    f"{status} {result.api_type.upper()}:",
                    f"    Requests/sec: {Fore.YELLOW}{result.requests_per_second:.2f}{Style.RESET_ALL}",
                    f"    Avg Response: {result.avg_response_time*1000:.2f}ms",
                    f"    Success Rate: {(result.success_count/result.total_requests)*100:.1f}%",
                    ""
                ])
        
        # Overall summary
        report_lines.extend([
            f"{Fore.CYAN}OVERALL PERFORMANCE RANKING{Style.RESET_ALL}",
            f"{'-' * 30}"
        ])
        
        # Calculate overall performance score (weighted average)
        api_scores = {}
        for result in results:
            if result.api_type not in api_scores:
                api_scores[result.api_type] = {
                    'total_rps': 0,
                    'total_success_rate': 0,
                    'count': 0
                }
            api_scores[result.api_type]['total_rps'] += result.requests_per_second
            api_scores[result.api_type]['total_success_rate'] += (result.success_count/result.total_requests)*100
            api_scores[result.api_type]['count'] += 1
        
        # Calculate averages and sort
        api_rankings = []
        for api_type, scores in api_scores.items():
            avg_rps = scores['total_rps'] / scores['count']
            avg_success = scores['total_success_rate'] / scores['count']
            overall_score = avg_rps * (avg_success / 100)  # Weight by success rate
            api_rankings.append((api_type, avg_rps, avg_success, overall_score))
        
        api_rankings.sort(key=lambda x: x[3], reverse=True)
        
        for i, (api_type, avg_rps, avg_success, score) in enumerate(api_rankings, 1):
            status = f"{Fore.GREEN}🏆{Style.RESET_ALL}" if i == 1 else f"{Fore.WHITE}{i}.{Style.RESET_ALL}"
            report_lines.extend([
                f"{status} {api_type.upper()}:",
                f"    Avg Requests/sec: {Fore.YELLOW}{avg_rps:.2f}{Style.RESET_ALL}",
                f"    Avg Success Rate: {avg_success:.1f}%",
                f"    Overall Score: {score:.2f}",
                ""
            ])
        
        report = "\n".join(report_lines)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                # Remove color codes for file output
                clean_report = report.replace(Fore.CYAN, '').replace(Fore.GREEN, '').replace(Fore.YELLOW, '').replace(Fore.WHITE, '').replace(Style.RESET_ALL, '')
                f.write(clean_report)
        
        return report
    
    @staticmethod
    def export_to_json(results: List[BenchmarkResult], output_file: str):
        """Export benchmark results to JSON"""
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
                'error_count': result.error_count,
                'error_rate': result.error_rate
            })
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

def get_csv_path() -> str:
    """Get the path to the users.csv file"""
    return str(Path(__file__).parent / "data" / "users.csv")