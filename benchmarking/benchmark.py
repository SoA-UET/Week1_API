#!/usr/bin/env python3
"""
API Benchmark Orchestrator
Runs performance benchmarks on all API types: REST, GraphQL, gRPC, and SOAP
"""
import sys
import os
import time
import signal
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
import argparse
import threading
import json
from datetime import datetime

# Add the app directory to Python path
app_dir = Path(__file__).parent / "app"
sys.path.append(str(app_dir))

def ensure_grpc_files():
    """Ensure gRPC protobuf files are generated"""
    grpc_dir = Path(__file__).parent / "app" / "gRPC"
    pb2_file = grpc_dir / "user_service_pb2.py"
    pb2_grpc_file = grpc_dir / "user_service_pb2_grpc.py"
    
    if not pb2_file.exists() or not pb2_grpc_file.exists():
        print("🔧 Generating missing gRPC protobuf files...")
        proto_file = grpc_dir / "proto" / "user_service.proto"
        
        if not proto_file.exists():
            print("❌ user_service.proto not found!")
            return False
        
        try:
            cmd = [
                sys.executable, "-m", "grpc_tools.protoc",
                f"--proto_path={proto_file.parent}",
                f"--python_out={grpc_dir}",
                f"--grpc_python_out={grpc_dir}",
                str(proto_file)
            ]
            
            result = subprocess.run(cmd, cwd=str(grpc_dir), capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ gRPC protobuf files generated successfully")
                return True
            else:
                print(f"❌ Failed to generate protobuf files: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error generating protobuf files: {e}")
            return False
    
    return True

# Ensure gRPC files exist before importing
if not ensure_grpc_files():
    print("Failed to generate gRPC protobuf files. gRPC benchmarks will be disabled.")

# Import benchmark clients
from REST.client import RESTBenchmark
from GraphQL.client import GraphQLBenchmark
try:
    from gRPC.client import gRPCBenchmark
    GRPC_AVAILABLE = True
except ImportError as e:
    print(f"Warning: gRPC client not available: {e}")
    gRPCBenchmark = None
    GRPC_AVAILABLE = False
    
from SOAP.client import SOAPBenchmark
from common.utils import BenchmarkResult, ReportGenerator

class ServerManager:
    """Manages starting and stopping API servers"""
    
    def __init__(self):
        self.servers = {}
        self.app_dir = Path(__file__).parent / "app"
    
    def start_server(self, api_type: str, port: int) -> subprocess.Popen:
        """Start a specific API server"""
        server_script = self.app_dir / api_type / "server.py"
        
        if not server_script.exists():
            raise FileNotFoundError(f"Server script not found: {server_script}")
        
        print(f"Starting {api_type} server on port {port}...")
        
        # Start server in a subprocess
        process = subprocess.Popen(
            [sys.executable, str(server_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(server_script.parent)
        )
        
        # Wait a bit for server to start
        time.sleep(3)
        
        # Check if process is still running
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            raise Exception(f"Failed to start {api_type} server: {stderr.decode()}")
        
        self.servers[api_type] = process
        print(f"✓ {api_type} server started (PID: {process.pid})")
        
        return process
    
    def stop_server(self, api_type: str):
        """Stop a specific API server"""
        if api_type in self.servers:
            process = self.servers[api_type]
            print(f"Stopping {api_type} server...")
            
            try:
                # Try graceful shutdown first
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if not responding
                process.kill()
                process.wait()
            
            del self.servers[api_type]
            print(f"✓ {api_type} server stopped")
    
    def stop_all_servers(self):
        """Stop all running servers"""
        for api_type in list(self.servers.keys()):
            self.stop_server(api_type)
    
    def wait_for_server(self, host: str, port: int, timeout: int = 30) -> bool:
        """Wait for server to be ready"""
        import socket
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                with socket.create_connection((host, port), timeout=1):
                    return True
            except (ConnectionRefusedError, OSError):
                time.sleep(0.5)
        
        return False

class BenchmarkOrchestrator:
    """Main benchmark orchestrator"""
    
    def __init__(self):
        self.server_manager = ServerManager()
        self.results = []
        
        # Server configurations
        self.server_configs = {
            "REST": {"port": 8000, "url": "http://localhost:8000"},
            "GraphQL": {"port": 8001, "url": "http://localhost:8001"},
            "gRPC": {"port": 50051, "url": "localhost:50051"},
            "SOAP": {"port": 8002, "url": "http://localhost:8002?wsdl"}
        }
        
        # Setup signal handler for cleanup
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print("\\nReceived shutdown signal. Cleaning up...")
        self.cleanup()
        sys.exit(0)
    
    def start_servers(self, apis: List[str] = None):
        """Start API servers"""
        if apis is None:
            apis = list(self.server_configs.keys())
        
        print("Starting API servers...")
        
        for api_type in apis:
            if api_type not in self.server_configs:
                print(f"Warning: Unknown API type {api_type}")
                continue
            
            try:
                config = self.server_configs[api_type]
                self.server_manager.start_server(api_type, config["port"])
                
                # Wait for server to be ready (except for gRPC which uses different protocol)
                if api_type != "gRPC":
                    if not self.server_manager.wait_for_server("localhost", config["port"]):
                        print(f"Warning: {api_type} server may not be ready")
                else:
                    # For gRPC, just wait a bit more
                    time.sleep(2)
                
            except Exception as e:
                print(f"Failed to start {api_type} server: {e}")
        
        print(f"Started {len(self.server_manager.servers)} servers")
        time.sleep(2)  # Extra wait time for all servers to be fully ready
    
    def run_benchmarks(self, apis: List[str] = None, num_requests: int = 100) -> List[BenchmarkResult]:
        """Run benchmarks on specified APIs"""
        if apis is None:
            apis = list(self.server_configs.keys())
        
        all_results = []
        
        # Create benchmark clients only for requested APIs
        benchmark_clients = {}
        
        for api_type in apis:
            try:
                if api_type == "REST":
                    benchmark_clients["REST"] = RESTBenchmark(self.server_configs["REST"]["url"])
                elif api_type == "GraphQL":
                    benchmark_clients["GraphQL"] = GraphQLBenchmark(self.server_configs["GraphQL"]["url"])
                elif api_type == "gRPC":
                    if GRPC_AVAILABLE and gRPCBenchmark:
                        benchmark_clients["gRPC"] = gRPCBenchmark(self.server_configs["gRPC"]["url"])
                    else:
                        print("Warning: gRPC requested but not available. Skipping gRPC benchmarks.")
                        continue
                elif api_type == "SOAP":
                    benchmark_clients["SOAP"] = SOAPBenchmark(self.server_configs["SOAP"]["url"])
                else:
                    print(f"Warning: Unknown API type {api_type}")
                    continue
            except Exception as e:
                print(f"Warning: Failed to create {api_type} benchmark client: {e}")
                continue
        
        for api_type in apis:
            if api_type not in benchmark_clients:
                print(f"Warning: No benchmark client for {api_type}")
                continue
            
            if api_type not in self.server_manager.servers:
                print(f"Warning: {api_type} server not running, skipping benchmarks")
                continue
            
            print(f"\\n{'='*60}")
            print(f"Running {api_type} API Benchmarks")
            print(f"{'='*60}")
            
            try:
                client = benchmark_clients[api_type]
                results = client.run_all_benchmarks(num_requests)
                all_results.extend(results)
                
                # Cleanup gRPC client
                if api_type == "gRPC" and hasattr(client, 'cleanup'):
                    client.cleanup()
                    
            except Exception as e:
                print(f"Failed to run {api_type} benchmarks: {e}")
        
        return all_results
    
    def generate_reports(self, results: List[BenchmarkResult], output_dir: Path = None):
        """Generate benchmark reports"""
        if not results:
            print("No results to generate reports from")
            return
        
        if output_dir is None:
            output_dir = Path(__file__).parent / "reports"
        
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Generate text report
        print("\\n" + "="*80)
        report = ReportGenerator.generate_comparison_report(results)
        print(report)
        
        # Save text report
        text_file = output_dir / f"benchmark_report_{timestamp}.txt"
        with open(text_file, 'w', encoding='utf-8') as f:
            clean_report = report.replace('\\x1b[0m', '').replace('\\x1b[32m', '').replace('\\x1b[33m', '').replace('\\x1b[36m', '').replace('\\x1b[37m', '')
            f.write(clean_report)
        
        # Export to JSON
        json_file = output_dir / f"benchmark_results_{timestamp}.json"
        ReportGenerator.export_to_json(results, str(json_file))
        
        print(f"\\nReports saved:")
        print(f"  Text report: {text_file}")
        print(f"  JSON data:   {json_file}")
    
    def cleanup(self):
        """Cleanup resources"""
        print("Cleaning up...")
        self.server_manager.stop_all_servers()
    
    def run_full_benchmark(self, apis: List[str] = None, num_requests: int = 100, 
                          output_dir: Path = None, keep_servers: bool = False):
        """Run complete benchmark suite"""
        try:
            print("API Performance Benchmark Suite")
            print("="*50)
            print(f"APIs: {apis or 'All (REST, GraphQL, gRPC, SOAP)'}")
            print(f"Requests per benchmark: {num_requests}")
            print(f"Output directory: {output_dir or 'reports/'}")
            print()
            
            # Start servers
            if not keep_servers:
                self.start_servers(apis)
            
            # Run benchmarks
            results = self.run_benchmarks(apis, num_requests)
            
            # Generate reports
            if results:
                self.generate_reports(results, output_dir)
                print(f"\\nBenchmark completed successfully with {len(results)} results!")
            else:
                print("\\nNo benchmark results were collected.")
            
        except KeyboardInterrupt:
            print("\\nBenchmark interrupted by user")
        except Exception as e:
            print(f"\\nBenchmark failed: {e}")
        finally:
            if not keep_servers:
                self.cleanup()

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="API Performance Benchmark Suite")
    
    parser.add_argument(
        "--apis", 
        nargs="+", 
        choices=["REST", "GraphQL", "gRPC", "SOAP"],
        help="APIs to benchmark (default: all)"
    )
    
    parser.add_argument(
        "--requests", 
        type=int, 
        default=100,
        help="Number of requests per benchmark (default: 100)"
    )
    
    parser.add_argument(
        "--output", 
        type=Path,
        help="Output directory for reports (default: ./reports)"
    )
    
    parser.add_argument(
        "--keep-servers", 
        action="store_true",
        help="Don't start/stop servers (assume they're already running)"
    )
    
    args = parser.parse_args()
    
    # Create orchestrator and run benchmarks
    orchestrator = BenchmarkOrchestrator()
    orchestrator.run_full_benchmark(
        apis=args.apis,
        num_requests=args.requests,
        output_dir=args.output,
        keep_servers=args.keep_servers
    )

if __name__ == "__main__":
    main()