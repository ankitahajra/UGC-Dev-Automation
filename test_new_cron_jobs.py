"""
Test script for new cron jobs 5 and 6
"""
import logging
from mock_cron_jobs import CronJobManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_cron_jobs():
    """Test the new cron jobs."""
    manager = CronJobManager()
    
    print("\n" + "="*80)
    print("Testing Cron Job 5: Missing Required Columns")
    print("="*80)
    result5 = manager.execute_job('cron-job-5')
    print(f"\nStatus: {result5['status']}")
    print(f"Error Type: {result5.get('error_type', 'N/A')}")
    if result5['status'] == 'failed':
        print(f"Error: {result5['error']}")
        print(f"\nError Details:")
        for key, value in result5['error_details'].items():
            print(f"  {key}: {value}")
        print(f"\nFix Suggestions:")
        for i, suggestion in enumerate(result5['fix_suggestions'], 1):
            print(f"  {i}. {suggestion}")
    
    print("\n" + "="*80)
    print("Testing Cron Job 6: Invalid Data Formats")
    print("="*80)
    result6 = manager.execute_job('cron-job-6')
    print(f"\nStatus: {result6['status']}")
    print(f"Error Type: {result6.get('error_type', 'N/A')}")
    if result6['status'] == 'failed':
        print(f"Error: {result6['error']}")
        print(f"\nError Details:")
        for key, value in result6['error_details'].items():
            if key != 'sample_errors':
                print(f"  {key}: {value}")
        
        if 'sample_errors' in result6['error_details']:
            print(f"\n  Sample Validation Errors:")
            for error in result6['error_details']['sample_errors']:
                print(f"    - Row {error['row']}, Customer {error['customer_id']}: {error['field']} = '{error['value']}' - {error['error']}")
        
        print(f"\nFix Suggestions:")
        for i, suggestion in enumerate(result6['fix_suggestions'], 1):
            print(f"  {i}. {suggestion}")
    
    print("\n" + "="*80)
    print("All Jobs Summary")
    print("="*80)
    jobs = manager.list_jobs()
    for job in jobs:
        print(f"\n{job['job_id']}: {job['name']}")
        print(f"  Status: {job['status']}")
        print(f"  Description: {job['description']}")

if __name__ == '__main__':
    test_cron_jobs()

# Made with Bob
