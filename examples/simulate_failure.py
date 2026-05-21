"""
Simulate Azure Function Failure
Sends a simulated failure event to the diagnostics webhook.
Use this to test the pipeline end-to-end.
"""

import requests
import json
import time
from datetime import datetime
import random

# Webhook endpoint
WEBHOOK_URL = "http://localhost:8080/diagnostics"

# Sample failure scenarios
FAILURE_SCENARIOS = [
    {
        "name": "Null Reference Exception",
        "functionName": "ProcessDataFunction",
        "invocationId": f"inv-{int(time.time())}-001",
        "exceptionMessage": "NullReferenceException: Object reference not set to an instance of an object",
        "stackTrace": """at DataProcessor.ProcessRequest(UserData userData) in /src/DataProcessor.cs:line 45
at Function.Run(HttpRequest req) in /src/Function.cs:line 23
at Microsoft.Azure.WebJobs.Host.Executors.FunctionExecutor.ExecuteAsync""",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "correlationId": f"corr-{int(time.time())}",
        "errorType": "NullReferenceException",
        "cpuUsage": 45.5,
        "memoryUsage": 256,
        "deploymentVersion": "1.2.3"
    },
    {
        "name": "Timeout Exception",
        "functionName": "ExternalApiFunction",
        "invocationId": f"inv-{int(time.time())}-002",
        "exceptionMessage": "TimeoutException: The operation has timed out after 5000ms",
        "stackTrace": """at System.Net.Http.HttpClient.SendAsync(HttpRequestMessage request)
at ApiClient.GetDataAsync() in /src/ApiClient.cs:line 67
at Function.Run(HttpRequest req) in /src/Function.cs:line 15""",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "correlationId": f"corr-{int(time.time())}",
        "errorType": "TimeoutException",
        "cpuUsage": 32.1,
        "memoryUsage": 189,
        "deploymentVersion": "1.2.3"
    },
    {
        "name": "Out of Memory",
        "functionName": "BatchProcessFunction",
        "invocationId": f"inv-{int(time.time())}-003",
        "exceptionMessage": "OutOfMemoryException: Insufficient memory to continue execution",
        "stackTrace": """at System.Collections.Generic.List.Add(T item)
at BatchProcessor.ProcessBatch(List items) in /src/BatchProcessor.cs:line 89
at Function.Run(HttpRequest req) in /src/Function.cs:line 31""",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "correlationId": f"corr-{int(time.time())}",
        "errorType": "OutOfMemoryException",
        "cpuUsage": 78.9,
        "memoryUsage": 512,
        "deploymentVersion": "1.2.3"
    },
    {
        "name": "Database Connection Error",
        "functionName": "DataAccessFunction",
        "invocationId": f"inv-{int(time.time())}-004",
        "exceptionMessage": "DatabaseConnectionException: Unable to connect to database server",
        "stackTrace": """at System.Data.SqlClient.SqlConnection.Open()
at DatabaseContext.OpenConnection() in /src/DatabaseContext.cs:line 34
at Function.Run(HttpRequest req) in /src/Function.cs:line 19""",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "correlationId": f"corr-{int(time.time())}",
        "errorType": "DatabaseConnectionException",
        "cpuUsage": 15.3,
        "memoryUsage": 128,
        "deploymentVersion": "1.2.3"
    }
]


def print_banner(text):
    """Print formatted banner"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def send_failure_event(scenario):
    """Send failure event to webhook"""
    print(f"Sending failure event: {scenario['name']}")
    print(f"  Function: {scenario['functionName']}")
    print(f"  Error: {scenario['errorType']}")
    print(f"  Invocation ID: {scenario['invocationId']}")
    
    try:
        response = requests.post(
            WEBHOOK_URL,
            json=scenario,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✓ Event sent successfully")
            print(f"  Status: {result.get('status', 'unknown')}")
            print(f"  Message: {result.get('message', 'N/A')}")
            return True
        else:
            print(f"\n✗ Failed to send event: HTTP {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"\n✗ Connection failed: Is the webhook server running?")
        print(f"  Start it with: python main.py webhook")
        return False
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        return False


def simulate_single_failure():
    """Simulate a single failure"""
    print_banner("Simulate Single Failure")
    
    print("Available failure scenarios:")
    for i, scenario in enumerate(FAILURE_SCENARIOS, 1):
        print(f"  {i}. {scenario['name']}")
    
    choice = input(f"\nSelect scenario (1-{len(FAILURE_SCENARIOS)}) or press Enter for random: ")
    
    if choice.strip():
        try:
            index = int(choice) - 1
            if 0 <= index < len(FAILURE_SCENARIOS):
                scenario = FAILURE_SCENARIOS[index]
            else:
                print("Invalid choice, using random scenario")
                scenario = random.choice(FAILURE_SCENARIOS)
        except ValueError:
            print("Invalid input, using random scenario")
            scenario = random.choice(FAILURE_SCENARIOS)
    else:
        scenario = random.choice(FAILURE_SCENARIOS)
    
    print()
    send_failure_event(scenario)


def simulate_multiple_failures():
    """Simulate multiple failures"""
    print_banner("Simulate Multiple Failures")
    
    count = input("How many failures to simulate? (default: 3): ")
    try:
        count = int(count) if count.strip() else 3
    except ValueError:
        count = 3
    
    interval = input("Interval between failures in seconds? (default: 2): ")
    try:
        interval = float(interval) if interval.strip() else 2
    except ValueError:
        interval = 2
    
    print(f"\nSimulating {count} failures with {interval}s interval...\n")
    
    for i in range(count):
        scenario = random.choice(FAILURE_SCENARIOS)
        # Update timestamp and IDs
        scenario['timestamp'] = datetime.utcnow().isoformat() + "Z"
        scenario['invocationId'] = f"inv-{int(time.time())}-{i+1:03d}"
        scenario['correlationId'] = f"corr-{int(time.time())}-{i+1:03d}"
        
        print(f"[{i+1}/{count}] ", end="")
        send_failure_event(scenario)
        
        if i < count - 1:
            print(f"\nWaiting {interval}s before next failure...")
            time.sleep(interval)
    
    print(f"\n✓ Simulated {count} failures")


def simulate_continuous_failures():
    """Simulate continuous failures"""
    print_banner("Simulate Continuous Failures")
    
    print("This will continuously send failure events.")
    print("Press Ctrl+C to stop.\n")
    
    interval = input("Interval between failures in seconds? (default: 5): ")
    try:
        interval = float(interval) if interval.strip() else 5
    except ValueError:
        interval = 5
    
    print(f"\nStarting continuous simulation (interval: {interval}s)...")
    print("Press Ctrl+C to stop\n")
    
    count = 0
    try:
        while True:
            count += 1
            scenario = random.choice(FAILURE_SCENARIOS)
            # Update timestamp and IDs
            scenario['timestamp'] = datetime.utcnow().isoformat() + "Z"
            scenario['invocationId'] = f"inv-{int(time.time())}-{count:03d}"
            scenario['correlationId'] = f"corr-{int(time.time())}-{count:03d}"
            
            print(f"[{count}] ", end="")
            send_failure_event(scenario)
            
            print(f"\nWaiting {interval}s...")
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print(f"\n\nStopped after {count} failures")


def test_webhook_health():
    """Test webhook health endpoint"""
    print_banner("Test Webhook Health")
    
    health_url = WEBHOOK_URL.replace('/diagnostics', '/health')
    
    print(f"Testing webhook health at {health_url}...")
    
    try:
        response = requests.get(health_url, timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✓ Webhook is healthy")
            print(f"  Status: {result.get('status', 'unknown')}")
            print(f"  Service: {result.get('service', 'N/A')}")
            print(f"  Timestamp: {result.get('timestamp', 'N/A')}")
            return True
        else:
            print(f"\n✗ Webhook returned HTTP {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"\n✗ Cannot connect to webhook")
        print(f"  Is the webhook server running?")
        print(f"  Start it with: python main.py webhook")
        return False
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        return False


def main():
    """Main menu"""
    print_banner("Azure Function Failure Simulator")
    
    print("This tool simulates Azure Function failures for testing.")
    print("Make sure the webhook server is running before proceeding.")
    print("Start it with: python main.py webhook\n")
    
    while True:
        print("\nOptions:")
        print("  1. Test webhook health")
        print("  2. Simulate single failure")
        print("  3. Simulate multiple failures")
        print("  4. Simulate continuous failures")
        print("  5. Exit")
        
        choice = input("\nSelect option (1-5): ")
        
        if choice == '1':
            test_webhook_health()
        elif choice == '2':
            simulate_single_failure()
        elif choice == '3':
            simulate_multiple_failures()
        elif choice == '4':
            simulate_continuous_failures()
        elif choice == '5':
            print("\nExiting...")
            break
        else:
            print("\nInvalid option, please try again")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {str(e)}")

# Made with Bob
