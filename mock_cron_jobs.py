"""
Mock Cron Job System with Various Failure Scenarios
Simulates different types of failures that can occur in production cron jobs.
Now reads from actual CSV files in mock_data/ directory.
"""

import logging
import time
import random
import csv
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

# Base path for mock data files
MOCK_DATA_DIR = Path(__file__).parent / 'mock_data'


class CronJobStatus(Enum):
    """Cron job execution status."""
    SUCCESS = "success"
    FAILED = "failed"
    RUNNING = "running"
    PENDING = "pending"


class FailureType(Enum):
    """Types of failures that can occur."""
    NULL_REFERENCE = "null_reference_error"
    MEMORY_OVERFLOW = "memory_overflow"
    TIMEOUT = "timeout_error"
    API_CONNECTION = "api_connection_error"
    DATABASE_LOCK = "database_lock_error"
    PERMISSION_DENIED = "permission_denied"
    INVALID_CONFIG = "invalid_configuration"
    RESOURCE_EXHAUSTED = "resource_exhausted"


class MockCronJob:
    """Base class for mock cron jobs with failure scenarios."""
    
    def __init__(self, job_id: str, name: str, description: str):
        """
        Initialize mock cron job.
        
        Args:
            job_id: Unique job identifier
            name: Job name
            description: Job description
        """
        self.job_id = job_id
        self.name = name
        self.description = description
        self.status = CronJobStatus.PENDING
        self.execution_history = []
        self.last_error = None
        self.last_execution_time = None
        
    def execute(self) -> Dict[str, Any]:
        """
        Execute the cron job.
        
        Returns:
            Execution result dictionary
        """
        raise NotImplementedError("Subclasses must implement execute method")
    
    def _record_execution(self, result: Dict[str, Any]) -> None:
        """Record execution in history."""
        execution_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'status': result['status'],
            'duration': result.get('duration', 0),
            'error': result.get('error'),
            'error_details': result.get('error_details')
        }
        self.execution_history.append(execution_record)
        self.last_execution_time = execution_record['timestamp']
        
        if result['status'] == 'failed':
            self.last_error = result.get('error')


class CronJob1_NullReferenceError(MockCronJob):
    """
    Cron Job 1: Null Reference Error
    Reads CSV file with null values and fails when accessing them.
    """
    
    def __init__(self, data_file='mock_data/customers_null_values.csv'):
        super().__init__(
            job_id="cron-job-1",
            name="Data Processing Job",
            description="Processes customer data from CSV - fails with null reference error"
        )
        self.failure_type = FailureType.NULL_REFERENCE
        self.data_file = data_file
        
    def execute(self) -> Dict[str, Any]:
        """Execute job with null reference error by reading CSV with null values."""
        start_time = time.time()
        self.status = CronJobStatus.RUNNING
        
        logger.info(f"Starting {self.name} (ID: {self.job_id})")
        
        try:
            # Read CSV file
            time.sleep(0.3)
            logger.info(f"Reading customer data from {self.data_file}...")
            
            csv_path = Path(self.data_file)
            if not csv_path.exists():
                csv_path = MOCK_DATA_DIR / Path(self.data_file).name
            
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    customer_id = row['customer_id']
                    
                    # This will fail when name is empty (row 2 in null_values.csv)
                    name = row['name']
                    if not name or name.strip() == '':
                        # Simulate accessing property of null object
                        name_upper = name.upper()  # Will work but is empty
                        name_parts = name.split()  # Empty list
                        first_name = name_parts[0]  # IndexError: list index out of range
                    
                    logger.info(f"Processing customer {customer_id}: {name}")
            
            result = {
                'status': 'success',
                'job_id': self.job_id,
                'duration': time.time() - start_time
            }
            
        except (TypeError, AttributeError, KeyError, IndexError) as e:
            duration = time.time() - start_time
            error_msg = f"Null reference error: {str(e)}"
            
            logger.error(f"{self.name} failed: {error_msg}")
            
            result = {
                'status': 'failed',
                'job_id': self.job_id,
                'duration': duration,
                'error': error_msg,
                'error_type': self.failure_type.value,
                'error_details': {
                    'line': 'first_name = name_parts[0]',
                    'variable': 'name',
                    'expected': 'non-empty string',
                    'actual': 'empty string',
                    'data_file': self.data_file,
                    'root_cause': 'CSV file contains empty/null values in required fields without validation',
                    'stack_trace': [
                        'File "mock_cron_jobs.py", line 120, in execute',
                        '  first_name = name_parts[0]',
                        'IndexError: list index out of range'
                    ]
                },
                'fix_suggestions': [
                    'Add null/empty check before processing name field',
                    'Implement data validation when reading CSV',
                    'Skip or log records with missing required fields',
                    'Use .get() method with default values for dict access'
                ]
            }
            self.status = CronJobStatus.FAILED
        
        self._record_execution(result)
        return result


class CronJob2_MemoryOverflow(MockCronJob):
    """
    Cron Job 2: Memory Overflow
    Reads large CSV file and loads all data into memory at once.
    """
    
    def __init__(self, data_file='mock_data/customers_large_volume.csv'):
        super().__init__(
            job_id="cron-job-2",
            name="Bulk Report Generation",
            description="Generates reports for all customers - fails with memory overflow"
        )
        self.failure_type = FailureType.MEMORY_OVERFLOW
        self.data_file = data_file
        
    def execute(self) -> Dict[str, Any]:
        """Execute job with memory overflow error by loading entire CSV."""
        start_time = time.time()
        self.status = CronJobStatus.RUNNING
        
        logger.info(f"Starting {self.name} (ID: {self.job_id})")
        
        records_count = 0
        try:
            # Read CSV file
            time.sleep(0.3)
            logger.info(f"Loading all customer records from {self.data_file}...")
            
            csv_path = Path(self.data_file)
            if not csv_path.exists():
                csv_path = MOCK_DATA_DIR / Path(self.data_file).name
            
            # BAD PRACTICE: Load entire file into memory
            all_customers = []
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Simulate loading large data
                    all_customers.append(row)
            
            # Simulate trying to process too much data
            # In reality, this would be millions of records
            logger.info(f"Loaded {len(all_customers)} records into memory")
            
            # Simulate memory overflow after loading data
            # Multiply data to simulate large volume
            expanded_data = []
            for i in range(100000):  # Simulate 100k iterations
                for customer in all_customers:
                    expanded_data.append({
                        **customer,
                        'iteration': i,
                        'large_field': 'x' * 10000  # 10KB per record
                    })
                    records_count = len(expanded_data)
                    
                    if records_count > 10000:  # Simulate memory limit
                        raise MemoryError(f"Out of memory: Cannot allocate memory for {records_count} records")
            
            result = {
                'status': 'success',
                'job_id': self.job_id,
                'duration': time.time() - start_time
            }
            
        except MemoryError as e:
            duration = time.time() - start_time
            error_msg = f"Memory overflow error: {str(e)}"
            
            logger.error(f"{self.name} failed: {error_msg}")
            
            result = {
                'status': 'failed',
                'job_id': self.job_id,
                'duration': duration,
                'error': error_msg,
                'error_type': self.failure_type.value,
                'error_details': {
                    'memory_used': '8.5 GB',
                    'memory_limit': '8 GB',
                    'records_attempted': records_count,
                    'records_processed': records_count,
                    'data_file': self.data_file,
                    'root_cause': 'Loading entire CSV into memory and expanding data without batch processing',
                    'stack_trace': [
                        'File "mock_cron_jobs.py", line 225, in execute',
                        '  expanded_data.append({...})',
                        'MemoryError: Out of memory: Cannot allocate memory for large dataset'
                    ]
                },
                'fix_suggestions': [
                    'Implement batch processing with pagination',
                    'Process CSV records in chunks (e.g., 1000 at a time)',
                    'Use streaming/iterator pattern instead of loading all data',
                    'Process and discard records instead of accumulating',
                    'Add memory monitoring and circuit breakers'
                ]
            }
            self.status = CronJobStatus.FAILED
        
        self._record_execution(result)
        return result


class CronJob3_TimeoutError(MockCronJob):
    """
    Cron Job 3: Timeout Error
    Simulates a job that fails due to exceeding execution time limit.
    """
    
    def __init__(self):
        super().__init__(
            job_id="cron-job-3",
            name="External API Sync",
            description="Syncs data with external API - fails with timeout"
        )
        self.failure_type = FailureType.TIMEOUT
        
    def execute(self) -> Dict[str, Any]:
        """Execute job with timeout error."""
        start_time = time.time()
        self.status = CronJobStatus.RUNNING
        
        logger.info(f"Starting {self.name} (ID: {self.job_id})")
        
        try:
            # Simulate API call that takes too long
            time.sleep(0.2)
            logger.info("Connecting to external API...")
            
            # Simulate timeout
            timeout_limit = 5  # seconds
            elapsed = time.time() - start_time
            
            if elapsed > timeout_limit or True:  # Force timeout for demo
                raise TimeoutError(f"Operation timed out after {timeout_limit} seconds")
            
            result = {
                'status': 'success',
                'job_id': self.job_id,
                'duration': time.time() - start_time
            }
            
        except TimeoutError as e:
            duration = time.time() - start_time
            error_msg = f"Timeout error: {str(e)}"
            
            logger.error(f"{self.name} failed: {error_msg}")
            
            result = {
                'status': 'failed',
                'job_id': self.job_id,
                'duration': duration,
                'error': error_msg,
                'error_type': self.failure_type.value,
                'error_details': {
                    'timeout_limit': '5 seconds',
                    'actual_duration': f'{duration:.2f} seconds',
                    'api_endpoint': 'https://external-api.example.com/sync',
                    'root_cause': 'External API response time exceeds configured timeout',
                    'stack_trace': [
                        'File "mock_cron_jobs.py", line 215, in execute',
                        '  response = api.sync_data(timeout=5)',
                        'TimeoutError: Operation timed out after 5 seconds'
                    ]
                },
                'fix_suggestions': [
                    'Increase timeout limit for external API calls',
                    'Implement retry logic with exponential backoff',
                    'Add circuit breaker pattern for failing APIs',
                    'Use async/non-blocking calls where possible',
                    'Add monitoring for API response times'
                ]
            }
            self.status = CronJobStatus.FAILED
        
        self._record_execution(result)
        return result


class CronJob4_DatabaseLockError(MockCronJob):
    """
    Cron Job 4: Database Lock Error
    Simulates a job that fails due to database locking issues.
    """
    
    def __init__(self):
        super().__init__(
            job_id="cron-job-4",
            name="Database Cleanup Job",
            description="Cleans up old records - fails with database lock"
        )
        self.failure_type = FailureType.DATABASE_LOCK
        
    def execute(self) -> Dict[str, Any]:
        """Execute job with database lock error."""
        start_time = time.time()
        self.status = CronJobStatus.RUNNING
        
        logger.info(f"Starting {self.name} (ID: {self.job_id})")
        
        try:
            time.sleep(0.3)
            logger.info("Acquiring database lock...")
            
            # Simulate database lock error
            raise Exception("Database lock timeout: Could not acquire lock on table 'customers' after 30 seconds")
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Database lock error: {str(e)}"
            
            logger.error(f"{self.name} failed: {error_msg}")
            
            result = {
                'status': 'failed',
                'job_id': self.job_id,
                'duration': duration,
                'error': error_msg,
                'error_type': self.failure_type.value,
                'error_details': {
                    'table': 'customers',
                    'lock_timeout': '30 seconds',
                    'conflicting_process': 'backup_job',
                    'root_cause': 'Multiple jobs trying to access same table simultaneously',
                    'stack_trace': [
                        'File "mock_cron_jobs.py", line 275, in execute',
                        '  db.execute("DELETE FROM customers WHERE...")',
                        'Exception: Database lock timeout'
                    ]
                },
                'fix_suggestions': [
                    'Implement job scheduling to avoid conflicts',
                    'Use row-level locking instead of table-level',
                    'Increase lock timeout threshold',
                    'Add retry logic with jitter',
                    'Consider using queue-based processing'
                ]
            }
            self.status = CronJobStatus.FAILED
        
        self._record_execution(result)
        return result


class CronJob5_MissingColumns(MockCronJob):
    """
    Cron Job 5: Missing Required Columns in CSV
    Reads CSV file that is missing required columns, causing schema mismatch.
    """
    
    def __init__(self, data_file='mock_data/customers_missing_columns.csv'):
        super().__init__(
            job_id="cron-job-5",
            name="Customer Data Validation Job",
            description="Validates customer data schema - fails with missing required columns"
        )
        self.failure_type = FailureType.INVALID_CONFIG
        self.data_file = data_file
        self.required_columns = ['customer_id', 'name', 'email', 'phone', 'status', 'created_date']
        
    def execute(self) -> Dict[str, Any]:
        """Execute job with missing columns error."""
        start_time = time.time()
        self.status = CronJobStatus.RUNNING
        
        logger.info(f"Starting {self.name} (ID: {self.job_id})")
        
        try:
            # Read CSV file
            time.sleep(0.3)
            logger.info(f"Validating CSV schema from {self.data_file}...")
            
            csv_path = Path(self.data_file)
            if not csv_path.exists():
                csv_path = MOCK_DATA_DIR / Path(self.data_file).name
            
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                actual_columns = reader.fieldnames or []
                
                # Check for missing columns
                missing_columns = [col for col in self.required_columns if col not in actual_columns]
                
                if missing_columns:
                    raise ValueError(f"CSV schema mismatch: Missing required columns: {missing_columns}")
                
                # If we get here, all columns exist
                for row in reader:
                    logger.info(f"Processing customer {row['customer_id']}")
            
            result = {
                'status': 'success',
                'job_id': self.job_id,
                'duration': time.time() - start_time
            }
            
        except ValueError as e:
            duration = time.time() - start_time
            error_msg = f"Invalid configuration: {str(e)}"
            
            logger.error(f"{self.name} failed: {error_msg}")
            
            # Determine which columns are missing
            csv_path = Path(self.data_file)
            if not csv_path.exists():
                csv_path = MOCK_DATA_DIR / Path(self.data_file).name
            
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                actual_columns = list(reader.fieldnames or [])
            
            missing_columns = [col for col in self.required_columns if col not in actual_columns]
            
            result = {
                'status': 'failed',
                'job_id': self.job_id,
                'duration': duration,
                'error': error_msg,
                'error_type': f"{self.failure_type.value} (missing_columns)",
                'error_details': {
                    'issue': 'CSV schema mismatch due to missing required columns',
                    'severity': 'high',
                    'impact': 'Job fails before processing because expected input contract is broken',
                    'missing_columns': missing_columns,
                    'expected_columns': self.required_columns,
                    'actual_columns': actual_columns,
                    'affected_component': self.data_file,
                    'root_cause': 'CSV file does not contain all required columns for processing',
                    'stack_trace': [
                        'File "mock_cron_jobs.py", line 450, in execute',
                        '  raise ValueError(f"CSV schema mismatch: Missing required columns: {missing_columns}")',
                        'ValueError: CSV schema mismatch'
                    ]
                },
                'fix_suggestions': [
                    'Add missing columns to the CSV file',
                    'Update CSV generation process to include all required fields',
                    'Implement schema validation before job execution',
                    'Add column mapping configuration for flexible schema',
                    'Use default values for optional columns'
                ]
            }
            self.status = CronJobStatus.FAILED
        
        self._record_execution(result)
        return result


class CronJob6_InvalidFormat(MockCronJob):
    """
    Cron Job 6: Invalid Data Formats in CSV Records
    Reads CSV file with malformed field values (invalid email, phone, date, status).
    """
    
    def __init__(self, data_file='mock_data/customers_invalid_format.csv'):
        super().__init__(
            job_id="cron-job-6",
            name="Customer Data Validation Job",
            description="Validates customer data formats - fails with invalid field values"
        )
        self.failure_type = FailureType.INVALID_CONFIG
        self.data_file = data_file
        
    def _validate_email(self, email: str) -> bool:
        """Validate email format."""
        return '@' in email and '.' in email.split('@')[1]
    
    def _validate_phone(self, phone: str) -> bool:
        """Validate phone format (must start with 555-)."""
        return phone.startswith('555-') and len(phone) == 8
    
    def _validate_date(self, date_str: str) -> bool:
        """Validate date format (YYYY-MM-DD)."""
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False
    
    def _validate_status(self, status: str) -> bool:
        """Validate status value (must be 'active' or 'inactive')."""
        return status.lower() in ['active', 'inactive']
        
    def execute(self) -> Dict[str, Any]:
        """Execute job with invalid format error."""
        start_time = time.time()
        self.status = CronJobStatus.RUNNING
        
        logger.info(f"Starting {self.name} (ID: {self.job_id})")
        
        validation_errors = []
        
        try:
            # Read CSV file
            time.sleep(0.3)
            logger.info(f"Validating customer data formats from {self.data_file}...")
            
            csv_path = Path(self.data_file)
            if not csv_path.exists():
                csv_path = MOCK_DATA_DIR / Path(self.data_file).name
            
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is line 1)
                    customer_id = row['customer_id']
                    
                    # Validate email
                    if not self._validate_email(row['email']):
                        validation_errors.append({
                            'row': row_num,
                            'customer_id': customer_id,
                            'field': 'email',
                            'value': row['email'],
                            'error': 'Invalid email format (missing @ or domain)'
                        })
                    
                    # Validate phone
                    if not self._validate_phone(row['phone']):
                        validation_errors.append({
                            'row': row_num,
                            'customer_id': customer_id,
                            'field': 'phone',
                            'value': row['phone'],
                            'error': 'Invalid phone format (should start with 555- and be 8 chars)'
                        })
                    
                    # Validate date
                    if not self._validate_date(row['created_date']):
                        validation_errors.append({
                            'row': row_num,
                            'customer_id': customer_id,
                            'field': 'created_date',
                            'value': row['created_date'],
                            'error': 'Invalid date format (should be YYYY-MM-DD)'
                        })
                    
                    # Validate status
                    if not self._validate_status(row['status']):
                        validation_errors.append({
                            'row': row_num,
                            'customer_id': customer_id,
                            'field': 'status',
                            'value': row['status'],
                            'error': "Invalid status (should be 'active' or 'inactive')"
                        })
            
            # If we found validation errors, raise exception
            if validation_errors:
                raise ValueError(f"Found {len(validation_errors)} validation errors in CSV data")
            
            result = {
                'status': 'success',
                'job_id': self.job_id,
                'duration': time.time() - start_time
            }
            
        except ValueError as e:
            duration = time.time() - start_time
            error_msg = f"Invalid configuration: {str(e)}"
            
            logger.error(f"{self.name} failed: {error_msg}")
            
            # Get first few errors for display
            sample_errors = validation_errors[:5]
            
            result = {
                'status': 'failed',
                'job_id': self.job_id,
                'duration': duration,
                'error': error_msg,
                'error_type': f"{self.failure_type.value} (invalid_format)",
                'error_details': {
                    'issue': 'Input records contain malformed field values',
                    'severity': 'high',
                    'impact': 'Job fails when parsing invalid email, phone, date, or status values',
                    'validation_rule': 'email/date/phone/status format validation',
                    'total_errors': len(validation_errors),
                    'sample_errors': sample_errors,
                    'affected_component': self.data_file,
                    'root_cause': 'CSV file contains records with invalid data formats that do not meet validation rules',
                    'stack_trace': [
                        'File "mock_cron_jobs.py", line 580, in execute',
                        '  raise ValueError(f"Found {len(validation_errors)} validation errors in CSV data")',
                        'ValueError: Found validation errors in CSV data'
                    ]
                },
                'fix_suggestions': [
                    'Implement data validation at data entry point',
                    'Add data cleansing/transformation before processing',
                    'Use regex patterns for format validation',
                    'Implement graceful error handling to skip invalid records',
                    'Add data quality monitoring and alerts',
                    'Create data validation rules documentation'
                ]
            }
            self.status = CronJobStatus.FAILED
        
        self._record_execution(result)
        return result


class CronJobManager:
    """Manages multiple cron jobs and their execution."""
    
    def __init__(self):
        """Initialize cron job manager."""
        self.jobs = {
            'cron-job-1': CronJob1_NullReferenceError(),
            'cron-job-2': CronJob2_MemoryOverflow(),
            'cron-job-3': CronJob3_TimeoutError(),
            'cron-job-4': CronJob4_DatabaseLockError(),
            'cron-job-5': CronJob5_MissingColumns(),
            'cron-job-6': CronJob6_InvalidFormat()
        }
        
    def list_jobs(self) -> List[Dict[str, Any]]:
        """
        List all available cron jobs.
        
        Returns:
            List of job information
        """
        return [
            {
                'job_id': job.job_id,
                'name': job.name,
                'description': job.description,
                'status': job.status.value,
                'last_execution': job.last_execution_time,
                'last_error': job.last_error
            }
            for job in self.jobs.values()
        ]
    
    def get_job(self, job_id: str) -> Optional[MockCronJob]:
        """
        Get a specific job by ID.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job instance or None
        """
        return self.jobs.get(job_id)
    
    def execute_job(self, job_id: str) -> Dict[str, Any]:
        """
        Execute a specific job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Execution result
        """
        job = self.get_job(job_id)
        if not job:
            return {
                'status': 'error',
                'message': f'Job {job_id} not found'
            }
        
        return job.execute()
    
    def get_job_history(self, job_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get execution history for a job.
        
        Args:
            job_id: Job identifier
            limit: Maximum number of records to return
            
        Returns:
            List of execution records
        """
        job = self.get_job(job_id)
        if not job:
            return []
        
        return job.execution_history[-limit:]


# Made with Bob