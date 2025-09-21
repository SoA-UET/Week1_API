#!/usr/bin/env python3
"""
Simple Working Benchmark Runner
Tests all APIs one by one with proper error handling
"""
import sys
import time
import threading
import subprocess
from pathlib import Path

# Add app to path
app_path = Path(__file__).parent / "app"
sys.path.append(str(app_path))

# Import simple clients
from REST.simple_client import SimpleRESTBenchmark
from GraphQL.simple_client import SimpleGraphQLBenchmark
from SOAP.simple_client import SimpleSOAPBenchmark
from gRPC.simple_client import SimplegRPCBenchmark
from common.simple_utils import SimpleReportGenerator

class SimpleServerManager:
    """Simple server management without complex subprocess handling"""
    
    def __init__(self):
        self.servers = {}
        self.server_threads = {}
    
    def start_rest_server(self):
        """Start REST server"""
        try:
            import subprocess
            from app.REST.server import app
            import uvicorn
            
            # Start in a thread to avoid blocking
            def run_server():
                uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")
            
            thread = threading.Thread(target=run_server, daemon=True)
            thread.start()
            self.server_threads['rest'] = thread
            
            # Wait a moment for server to start
            time.sleep(2)
            return True
            
        except Exception as e:
            print(f"Failed to start REST server: {e}")
            return False
    
    def start_graphql_server(self):
        """Start GraphQL server"""
        try:
            from app.GraphQL.simple_server import app
            import uvicorn
            
            # Start in a thread
            def run_server():
                uvicorn.run(app, host="127.0.0.1", port=8001, log_level="warning")
            
            thread = threading.Thread(target=run_server, daemon=True)
            thread.start()
            self.server_threads['graphql'] = thread
            
            # Wait a moment for server to start
            time.sleep(2)
            return True
            
        except Exception as e:
            print(f"Failed to start GraphQL server: {e}")
            return False
    
    def start_soap_server(self):
        """Start SOAP server"""
        try:
            from app.SOAP.simple_server import run_server
            
            # Start in a thread
            def run_soap():
                server = run_server()
                server.serve_forever()
            
            thread = threading.Thread(target=run_soap, daemon=True)
            thread.start()
            self.server_threads['soap'] = thread
            
            # Wait a moment for server to start
            time.sleep(3)
            return True
            
        except Exception as e:
            print(f"Failed to start SOAP server: {e}")
            return False
    
    def start_grpc_server(self):
        """Start gRPC server"""
        try:
            from app.gRPC.simple_server import serve
            
            # Start in a thread
            def run_grpc():
                server = serve()
                if server:
                    try:
                        while True:
                            time.sleep(1)
                    except KeyboardInterrupt:
                        server.stop(0)
            
            thread = threading.Thread(target=run_grpc, daemon=True)
            thread.start()
            self.server_threads['grpc'] = thread
            
            # Wait a moment for server to start
            time.sleep(3)
            return True
            
        except Exception as e:
            print(f"Failed to start gRPC server: {e}")
            return False
    
    def test_server(self, url: str) -> bool:
        """Test if server is responding"""
        try:
            import requests
            response = requests.get(url, timeout=5)
            return response.status_code < 500
        except:
            return False
        """Test if server is responding"""
        try:
            import requests
            response = requests.get(url, timeout=5)
            return response.status_code < 500
        except:
            return False

def main():
    """Main benchmark runner"""
    print("🚀 Starting Simple API Benchmarks")
    print("=" * 50)
    
    # Initialize components
    manager = SimpleServerManager()
    report_gen = SimpleReportGenerator()
    all_results = []
    
    # Test REST API
    print("\n📊 Testing REST API...")
    if manager.start_rest_server():
        time.sleep(3)  # Give server time to fully start
        
        if manager.test_server("http://localhost:8000/users"):
            print("✅ REST server is running")
            try:
                benchmark = SimpleRESTBenchmark()
                results = benchmark.run_all_benchmarks(30)  # Smaller number for faster testing
                all_results.extend(results)
                print(f"✅ REST benchmarks completed: {len(results)} tests")
            except Exception as e:
                print(f"❌ REST benchmark failed: {e}")
        else:
            print("❌ REST server not responding")
    else:
        print("❌ Failed to start REST server")
    
    # Test GraphQL API
    print("\n📊 Testing GraphQL API...")
    if manager.start_graphql_server():
        time.sleep(3)  # Give server time to fully start
        
        # GraphQL endpoints typically return 405 for GET requests, so we test differently
        print("✅ GraphQL server started")
        try:
            benchmark = SimpleGraphQLBenchmark()
            results = benchmark.run_all_benchmarks(30)
            all_results.extend(results)
            print(f"✅ GraphQL benchmarks completed: {len(results)} tests")
        except Exception as e:
            print(f"❌ GraphQL benchmark failed: {e}")
    else:
        print("❌ Failed to start GraphQL server")
    
    # Test SOAP API
    print("\n📊 Testing SOAP API...")
    if manager.start_soap_server():
        # Test if SOAP WSDL is available
        if manager.test_server("http://localhost:8002?wsdl"):
            print("✅ SOAP server is running")
            try:
                benchmark = SimpleSOAPBenchmark()
                results = benchmark.run_all_benchmarks(20)  # Smaller for SOAP
                all_results.extend(results)
                print(f"✅ SOAP benchmarks completed: {len(results)} tests")
            except Exception as e:
                print(f"❌ SOAP benchmark failed: {e}")
        else:
            print("❌ SOAP server not responding")
    else:
        print("❌ Failed to start SOAP server")
    
    # Test gRPC API
    print("\n📊 Testing gRPC API...")
    if manager.start_grpc_server():
        print("✅ gRPC server started")
        try:
            benchmark = SimplegRPCBenchmark()
            results = benchmark.run_all_benchmarks(20)  # Smaller for gRPC
            all_results.extend(results)
            print(f"✅ gRPC benchmarks completed: {len(results)} tests")
        except Exception as e:
            print(f"❌ gRPC benchmark failed: {e}")
    else:
        print("❌ Failed to start gRPC server")
    
    # Generate reports
    print("\n📊 Generating Reports...")
    if all_results:
        report_gen.generate_reports(all_results)
        print(f"✅ Generated reports for {len(all_results)} benchmark results")
        
        # Quick summary
        print("\n📈 Quick Summary:")
        for result in all_results:
            if result:
                print(f"  {result.api_type} - {result.operation}: "
                     f"{result.avg_response_time:.4f}s avg, "
                     f"{result.success_rate:.1%} success")
    else:
        print("❌ No benchmark results to report")
    
    print("\n🎉 Benchmark completed!")
    print("Check 'benchmark_report.json' and 'benchmark_report.txt' for detailed results")

if __name__ == "__main__":
    main()