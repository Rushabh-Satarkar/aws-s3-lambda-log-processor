import json
import os
import boto3
from datetime import datetime

s3 = boto3.client('s3')

# Environment variables (set in Lambda configuration)
PROCESSED_BUCKET = os.environ.get('PROCESSED_BUCKET')

def lambda_handler(event, context):
    print(f"Received event: {json.dumps(event)}")

    for record in event['Records']:
        bucket_name = record['s3']['bucket']['name']
        object_key = record['s3']['object']['key']

        print(f"Processing file: s3://{bucket_name}/{object_key}")

        try:
            # 1. Read the log file from the raw bucket
            response = s3.get_object(Bucket=bucket_name, Key=object_key)
            file_content = response['Body'].read().decode('utf-8')

            processed_logs = []
            failed_logs = []

            # Assuming each line is a separate JSON log entry
            for line in file_content.splitlines():
                if not line.strip():
                    continue
                try:
                    log_entry = json.loads(line)

                    # 2. Perform Validation
                    # Example: Check for 'level' and 'message' fields
                    if 'level' in log_entry and 'message' in log_entry:
                        log_entry['processed_timestamp'] = datetime.now().isoformat()
                        processed_logs.append(log_entry)
                    else:
                        print(f"Validation failed for log entry (missing required fields): {line}")
                        failed_logs.append(log_entry) # Or write to a separate error S3 bucket

                except json.JSONDecodeError:
                    print(f"Failed to parse JSON line: {line}")
                    failed_logs.append({"raw_log": line, "error": "JSONDecodeError"})

            # 3. Write validated logs to the processed bucket
            if processed_logs:
                processed_filename = f"processed/{object_key.replace('.log', '')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
                s3.put_object(
                    Bucket=PROCESSED_BUCKET,
                    Key=processed_filename,
                    Body=json.dumps(processed_logs, indent=2) # Store as JSON array for simplicity
                )
                print(f"Successfully processed and stored {len(processed_logs)} logs to s3://{PROCESSED_BUCKET}/{processed_filename}")

            if failed_logs:
                error_filename = f"errors/{object_key.replace('.log', '')}_{datetime.now().strftime('%Y%m%d%H%M%S')}_errors.json"
                s3.put_object(
                    Bucket=PROCESSED_BUCKET, # Or a dedicated error bucket
                    Key=error_filename,
                    Body=json.dumps(failed_logs, indent=2)
                )
                print(f"Stored {len(failed_logs)} failed logs to s3://{PROCESSED_BUCKET}/{error_filename}")

        except Exception as e:
            print(f"Error processing {object_key}: {e}")
            raise # Re-raise to indicate failure to S3 trigger

    return {
        'statusCode': 200,
        'body': json.dumps('Log processing completed!')
    }
