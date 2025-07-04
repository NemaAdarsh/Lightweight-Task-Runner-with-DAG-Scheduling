"""
Example task functions for demonstration purposes.
"""

import time
import random
import os
from typing import Any


def hello_world(name: str = "World") -> str:
    """Simple hello world task."""
    message = f"Hello, {name}!"
    print(message)
    return message


def process_data(input_data: str, multiplier: int = 2) -> str:
    """Simulate data processing with some delay."""
    print(f"Processing data: {input_data}")
    
    # Simulate processing time
    time.sleep(random.uniform(1, 3))
    
    result = f"Processed: {input_data} x{multiplier}"
    print(f"Processing complete: {result}")
    return result


def validate_output(data: str) -> bool:
    """Validate processed data."""
    print(f"Validating: {data}")
    
    # Simulate validation time
    time.sleep(random.uniform(0.5, 1.5))
    
    # Random validation result for demo
    is_valid = len(data) > 10
    print(f"Validation result: {'PASS' if is_valid else 'FAIL'}")
    
    if not is_valid:
        raise ValueError(f"Validation failed for: {data}")
    
    return is_valid


def create_report(data1: str, data2: str) -> str:
    """Create a summary report from multiple data sources."""
    print(f"Creating report from: {data1}, {data2}")
    
    # Simulate report generation
    time.sleep(random.uniform(1, 2))
    
    report = f"REPORT\\n========\\nData 1: {data1}\\nData 2: {data2}\\nGenerated at: {time.ctime()}"
    print("Report generated successfully")
    return report


def save_to_file(content: str, filename: str = "output.txt") -> str:
    """Save content to a file."""
    print(f"Saving content to: {filename}")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with open(filename, 'w') as f:
        f.write(content)
    
    print(f"Content saved to: {filename}")
    return filename


def cleanup_temp_files(pattern: str = "temp_*") -> int:
    """Clean up temporary files."""
    print(f"Cleaning up files matching: {pattern}")
    
    # Simulate cleanup
    time.sleep(0.5)
    
    # Return number of files cleaned (simulated)
    cleaned_count = random.randint(0, 5)
    print(f"Cleaned up {cleaned_count} temporary files")
    return cleaned_count


def send_notification(message: str, recipient: str = "admin") -> bool:
    """Send notification (simulated)."""
    print(f"Sending notification to {recipient}: {message}")
    
    # Simulate network delay
    time.sleep(random.uniform(0.2, 0.8))
    
    # Random success/failure for demo
    success = random.random() > 0.1  # 90% success rate
    
    if success:
        print("Notification sent successfully")
    else:
        print("Failed to send notification")
        raise RuntimeError("Notification service unavailable")
    
    return success


def fetch_external_data(source: str, timeout: int = 10) -> dict:
    """Fetch data from external source (simulated)."""
    print(f"Fetching data from: {source}")
    
    # Simulate network request
    time.sleep(random.uniform(1, 3))
    
    # Simulate occasional failures
    if random.random() < 0.05:  # 5% failure rate
        raise ConnectionError(f"Failed to connect to {source}")
    
    data = {
        "source": source,
        "timestamp": time.time(),
        "records": random.randint(100, 1000),
        "status": "success"
    }
    
    print(f"Fetched {data['records']} records from {source}")
    return data


def aggregate_results(*results: Any) -> dict:
    """Aggregate multiple task results."""
    print(f"Aggregating {len(results)} results")
    
    aggregated = {
        "total_inputs": len(results),
        "results": list(results),
        "aggregated_at": time.ctime(),
        "summary": f"Processed {len(results)} items successfully"
    }
    
    print(f"Aggregation complete: {aggregated['summary']}")
    return aggregated


def long_running_task(duration: int = 30) -> str:
    """Simulate a long-running task."""
    print(f"Starting long-running task (duration: {duration}s)")
    
    for i in range(duration):
        time.sleep(1)
        if i % 5 == 0:
            print(f"Progress: {i}/{duration} seconds")
    
    result = f"Long-running task completed after {duration} seconds"
    print(result)
    return result


def failing_task(failure_rate: float = 0.5) -> str:
    """Task that fails randomly for testing retry logic."""
    print(f"Executing task with {failure_rate*100}% failure rate")
    
    if random.random() < failure_rate:
        error_message = "Simulated task failure"
        print(f"Task failed: {error_message}")
        raise RuntimeError(error_message)
    
    result = "Task completed successfully despite risk of failure"
    print(result)
    return result
