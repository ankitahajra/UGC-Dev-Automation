# Mock Data Files for Cron Job Testing

This directory contains sample CSV files with various failure scenarios for testing the cron job auto-fix system.

## Available Data Files

### 1. `customers_valid.csv` ✅
**Purpose:** Valid data for successful processing
- 5 records with all required fields
- Proper data formats
- Use this to test successful job execution

### 2. `customers_missing_columns.csv` ❌
**Purpose:** Missing required columns
- Missing: `phone`, `status`, `created_date` columns
- **Triggers:** KeyError when accessing missing columns
- **Tests:** Column validation and error handling

### 3. `customers_null_values.csv` ❌
**Purpose:** Null/empty values in critical fields
- Row 2: Empty name field
- Row 3: Empty email field
- Row 4: Empty phone field
- Row 5: All fields empty
- **Triggers:** NullReferenceError, validation failures
- **Tests:** Null value handling

### 4. `customers_large_volume.csv` ⚠️
**Purpose:** Large data volume simulation
- 10 records with large text fields (200+ chars each)
- Simulates memory pressure
- **Triggers:** Memory issues when loading all at once
- **Tests:** Batch processing, memory management

### 5. `customers_invalid_format.csv` ❌
**Purpose:** Invalid data formats
- Row 1: Invalid email format
- Row 2: Invalid date format
- Row 3: Invalid phone format
- Row 4: Invalid status value
- Row 5: Impossible date (2024-13-99)
- **Triggers:** Validation errors, parsing failures
- **Tests:** Data validation, format checking

## How to Use These Files

### In Your Cron Jobs:
```python
import csv

# Read the file
with open('mock_data/customers_null_values.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        # This will fail when accessing null values
        customer_id = row['customer_id']
        name = row['name']  # Will be empty string for some rows
        if not name:
            raise ValueError(f"Customer {customer_id} has no name")
```

### Testing Different Scenarios:
1. **Test Null Handling:** Use `customers_null_values.csv`
2. **Test Missing Columns:** Use `customers_missing_columns.csv`
3. **Test Data Validation:** Use `customers_invalid_format.csv`
4. **Test Memory Issues:** Use `customers_large_volume.csv`
5. **Test Success Case:** Use `customers_valid.csv`

## File Specifications

### CSV Format:
- **Delimiter:** Comma (,)
- **Encoding:** UTF-8
- **Headers:** First row contains column names

### Expected Columns:
- `customer_id` (integer)
- `name` (string)
- `email` (string, email format)
- `phone` (string, format: 555-XXXX)
- `status` (string, values: active/inactive)
- `created_date` (string, format: YYYY-MM-DD)
- `notes` (string, optional, only in large_volume file)

## Creating Your Own Test Data

To add more test scenarios:

1. Create a new CSV file in this directory
2. Include the failure scenario you want to test
3. Update this README with the new file description
4. Reference it in your cron job code

## Example Failure Scenarios to Add:

- **Duplicate Records:** Same customer_id multiple times
- **Encoding Issues:** Special characters, UTF-8 problems
- **Malformed CSV:** Missing quotes, extra commas
- **Empty File:** Zero records
- **Header Only:** Headers but no data rows
- **Wrong Delimiter:** Tab-separated instead of comma
- **Binary Data:** Non-text content in CSV

## Integration with Cron Jobs

Update your cron job to accept a file path parameter:

```python
class CronJobWithFileInput(MockCronJob):
    def __init__(self, data_file='mock_data/customers_valid.csv'):
        self.data_file = data_file
        # ... rest of init
    
    def execute(self):
        # Read and process the file
        with open(self.data_file, 'r') as f:
            # Process data
            pass
```

This allows testing different failure scenarios by changing the input file!