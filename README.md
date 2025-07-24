# AWS S3 & Lambda Event-Driven Log Processor

This project demonstrates an event-driven data workflow on Amazon Web Services (AWS) using S3 and Lambda to process and validate incoming log files, making them queryable via AWS Athena. It's designed with AWS Free Tier considerations in mind, making it suitable for learning and personal projects.

## Architecture Diagram

A visual representation of the data flow:

```mermaid
graph TD
    A[Log Source: Upload Log File] --> B{S3 Bucket: Raw Logs};

    B -- ObjectCreated Event --> C[AWS Lambda: LogProcessorValidator Invocation];

    subgraph AWS Lambda Processing
        C --> D[Lambda: Read Log File from Raw S3];
        D --> E{Lambda: Parse Log Entries};
        E --> F{Lambda: Validate Log Entry};

        F -- Validated --> G[Lambda: Add 'processed_timestamp'];
        G --> H[Lambda: Write Processed Log to S3\n(processed/)];

        F -- Invalid/Error --> I[Lambda: Write Failed Log to S3\n(errors/)];
    end

    H --> J(S3 Bucket: Processed Logs);
    I --> J;

    J --> K[AWS Glue Crawler: LogProcessorCrawler\n(Run on Demand)];
    K --> L[AWS Glue Data Catalog: log_analytics_db\n(Table Definitions)];

    L --> M[Amazon Athena: SQL Query Execution];
    M --> N[S3 Bucket: Athena Query Results];

    C --> O[Amazon CloudWatch Logs: Lambda Logs];
    M --> P[Data Analysts/Reporting Tools];


# aws-s3-lambda-log-processor

Project Overview
This project showcases a fundamental cloud-native data engineering pattern:

Event-Driven Ingestion: New log files arriving in an S3 bucket trigger a serverless function.

Serverless Processing: AWS Lambda performs validation and transformation without requiring server management.

Data Lake Storage: Processed and raw data reside in S3, providing scalable and cost-effective storage.

Metadata Management: AWS Glue Data Catalog stores schemas, enabling easy querying.

Interactive Querying: Amazon Athena allows direct SQL queries on S3 data, ideal for analytics and reporting.

AWS Services Used
Amazon S3: For raw log ingestion and storing processed/error logs, and Athena query results.

AWS Lambda: Serverless compute for processing and validation logic.

AWS Glue Data Catalog: Metadata repository, populated by a Glue Crawler.

AWS Glue Crawler: Automatically infers schema from S3 data.

Amazon Athena: Interactive query service for running SQL queries on S3 data.

Amazon CloudWatch Logs: For monitoring and debugging Lambda function execution.

Setup Instructions (Step-by-Step Guide)
Prerequisites:

An AWS Account (Free Tier eligible).

AWS CLI configured (optional, but helpful for programmatic interaction).

Basic understanding of AWS S3, Lambda, Glue, and Athena.

AWS Account Setup:

Create an AWS account if you don't have one. Monitor your billing dashboard regularly.

Choose a preferred AWS Region (e.g., us-east-1, ap-south-1).

(Optional but Recommended) Create an IAM user with appropriate permissions (AmazonS3FullAccess, AWSLambda_FullAccess, AWSGlueConsoleFullAccess, AmazonAthenaFullAccess) and use its credentials.

Create S3 Buckets:

Create two S3 buckets in your chosen region:

my-log-ingestion-raw-bucket-<yourname>-<suffix> (for raw logs)

my-log-ingestion-processed-bucket-<yourname>-<suffix> (for processed, validated, and error logs, and Athena results)

Ensure default settings (ACLs disabled, block public access enabled).

Develop the Lambda Function (LogProcessorValidator):

Go to Lambda console -> "Create function".

Name: LogProcessorValidator

Runtime: Python 3.9 (or newer)

Architecture: arm64

Execution Role: "Create a new role with basic Lambda permissions".

Configure Lambda Permissions (IAM Role):

Go to the function's "Configuration" -> "Permissions" -> Click on the Role Name.

Attach an inline policy or update the existing one to grant:

s3:GetObject on arn:aws:s3:::your-raw-bucket-name/*

s3:PutObject on arn:aws:s3:::your-processed-bucket-name/*

Ensure logs:CreateLogGroup, logs:CreateLogStream, logs:PutLogEvents are present (usually covered by AWSLambdaBasicExecutionRole).

Upload Code: Copy the lambda_function.py content from this repository into the Lambda code editor and "Deploy".

Configure Environment Variables: Add PROCESSED_BUCKET with the value of your processed bucket name.

Adjust Settings: Set memory to 128 MB and timeout to 1-5 minutes under "General configuration".

Configure S3 Event Trigger:

Go to your my-log-ingestion-raw-bucket-... in S3 console.

Under "Properties" -> "Event notifications", click "Create event notification".

Name: TriggerLambdaOnLogUpload

Suffix: .log

Event types: "All object create events".

Destination: "Lambda function", select LogProcessorValidator.

Test the Workflow:

Create a local sample_log.log file with the provided sample content.

Upload sample_log.log to your my-log-ingestion-raw-bucket-... S3 bucket.

Monitor Lambda's "Monitor" tab and "View logs in CloudWatch" for execution status and logs.

Verify the output files in your my-log-ingestion-processed-bucket-... (processed/ and errors/ folders).

Create AWS Glue Data Catalog Tables:

Go to Glue console -> "Databases" -> "Add database" (name: log_analytics_db).

Go to Glue console -> "Crawlers" -> "Create crawler".

Name: LogProcessorCrawler

Data stores: Add paths for s3://my-log-ingestion-processed-bucket-.../processed/ and s3://my-log-ingestion-processed-bucket-.../errors/.

IAM Role: "Create new IAM role" (e.g., AWSGlueServiceRoleForLogs).

Frequency: "Run on demand".

Output: log_analytics_db.

Run the LogProcessorCrawler and wait for it to complete.

Query Data with Amazon Athena:

Go to Athena console.

Set query result location (e.g., s3://my-log-ingestion-processed-bucket-.../athena-query-results/).

Select log_analytics_db as your database.

Run sample queries:

SQL

SELECT * FROM "log_analytics_db"."processed_logs" LIMIT 10;
SELECT level, COUNT(*) AS log_count FROM "log_analytics_db"."processed_logs" GROUP BY level;
SELECT * FROM "log_analytics_db"."errors_logs" LIMIT 10;
Project Cleanup (Crucial for Free Tier)
To avoid unexpected charges, always delete all resources after you're done experimenting:

Delete Athena tables (processed_logs, errors_logs) and then the log_analytics_db database in Athena/Glue.

Delete the LogProcessorCrawler in AWS Glue.

Delete the LogProcessorValidator Lambda function.

Empty and then delete both S3 buckets (raw and processed).

Delete any custom IAM roles or policies created for Lambda and Glue.

Future Enhancements
Advanced Validation: Implement more complex data quality checks (e.g., regex matching, range checks).

Error Handling: Implement dead-letter queues (DLQs) for failed Lambda invocations.

Data Formats: Write processed data to optimized formats like Parquet or ORC for better Athena performance.

Orchestration: Introduce AWS Step Functions for more complex stateful workflows, or consider AWS MWAA for scheduled, complex pipelines using Airflow if scaling beyond serverless is needed.

Infrastructure as Code (IaC): Use AWS CloudFormation or Terraform to define and deploy all resources programmatically.

Alerting & Monitoring: Set up CloudWatch alarms for Lambda errors, S3 bucket size, or Athena query costs.

Event-driven log processing and validation on AWS using S3 and Lambda, with Athena for querying.
