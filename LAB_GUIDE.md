# AWS S3 Data Intelligence with Cortex AI Functions, Search, Analyst & Agents

## Hands-On Lab Guide

---

## Overview

**Duration:** ~90 minutes

In this lab you will build a complete data intelligence pipeline that:
1. Auto-ingests files from Amazon S3 into Snowflake via Snowpipe
2. Processes them through 11 Cortex AI functions (parse, transcribe, extract, classify, sentiment, summarize, translate, redact, complete, embed)
3. Exposes everything through Cortex Search (semantic retrieval), Cortex Analyst (natural-language-to-SQL), and a Cortex Agent (unified chat)
4. Makes it accessible via Snowflake Intelligence as a chat UI

Healthcare documents are used as the example dataset, but the patterns apply to any domain.

### What You'll Build

```
S3 Bucket (pdfs/, txt/, audio/)
        |
  S3 Event Notification → SQS (Snowflake-managed)
        |
  Snowpipe (x3) → FILES_LOG → Stream → Task
        |
  Stored Procedures (AI function chains)
        |
  Intelligence Tables (PDF, TXT, Audio)
        |
  ┌─────────────────────────────────────┐
  │  Cortex Search (3 services)         │
  │  Cortex Analyst (Semantic View)     │
  │  Cortex Agent (4 tools)             │
  │  Snowflake Intelligence (chat UI)   │
  └─────────────────────────────────────┘
```

---

## Prerequisites

- [ ] Snowflake account with **ACCOUNTADMIN** role
- [ ] Cortex AI functions enabled in your region
- [ ] AWS account with permissions to create S3 buckets, IAM roles, and event notifications
- [ ] AWS CLI installed (`brew install awscli` on Mac, or use AWS Console)

### Regional Note

This lab uses `mistral-large2` for AI_COMPLETE. If your region supports `claude-3-5-sonnet`, you may use it instead.

Verify cross-region is enabled:
```sql
SHOW PARAMETERS LIKE 'CORTEX_ENABLED_CROSS_REGION' IN ACCOUNT;
-- Should show 'ANY_REGION'. If 'DISABLED', run:
-- ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION';
```

---

## Step 1: Create Snowflake Database & Warehouse

**Duration:** 2 minutes

Open a Snowsight worksheet and run:

```sql
USE ROLE ACCOUNTADMIN;

-- Database
CREATE OR REPLACE DATABASE HEALTHCARE_AI_DEMO
  COMMENT = 'Healthcare AI Intelligence Pipeline';

-- Three schemas for separation of concerns
CREATE SCHEMA IF NOT EXISTS HEALTHCARE_AI_DEMO.RAW;
CREATE SCHEMA IF NOT EXISTS HEALTHCARE_AI_DEMO.PROCESSED;
CREATE SCHEMA IF NOT EXISTS HEALTHCARE_AI_DEMO.ANALYTICS;

-- Warehouse
CREATE OR REPLACE WAREHOUSE HEALTHCARE_AI_WH
  WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE;

USE WAREHOUSE HEALTHCARE_AI_WH;

-- Verify
SHOW SCHEMAS IN DATABASE HEALTHCARE_AI_DEMO;
```

---

## Step 2: Create S3 Bucket (AWS)

**Duration:** 5 minutes

### Option A: AWS Console

1. Go to **S3** in the AWS Console
2. Click **Create bucket**
3. Bucket name: `healthcare-ai-demo-<your-initials>` (must be globally unique)
4. Region: **eu-central-1** (or same region as your Snowflake account)
5. Leave all other settings as default, click **Create bucket**
6. Open the bucket and create 3 folders:
   - `healthcare/pdfs/`
   - `healthcare/txt/`
   - `healthcare/audio/`

### Option B: AWS CLI

```bash
BUCKET_NAME="healthcare-ai-demo-<your-initials>"
AWS_REGION="eu-central-1"

aws s3 mb s3://$BUCKET_NAME --region $AWS_REGION

aws s3api put-object --bucket $BUCKET_NAME --key healthcare/pdfs/
aws s3api put-object --bucket $BUCKET_NAME --key healthcare/txt/
aws s3api put-object --bucket $BUCKET_NAME --key healthcare/audio/
```

> **Write down your bucket name** — you'll need it in the next steps.

---

## Step 3: Create IAM Role for Snowflake (AWS)

**Duration:** 10 minutes

### 3a. Create IAM Policy

In the **AWS Console** → **IAM** → **Policies** → **Create policy** → **JSON**:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:GetObjectVersion",
        "s3:ListBucket",
        "s3:GetBucketLocation"
      ],
      "Resource": [
        "arn:aws:s3:::<YOUR_BUCKET_NAME>",
        "arn:aws:s3:::<YOUR_BUCKET_NAME>/*"
      ]
    }
  ]
}
```

Name it: `SnowflakeHealthcareS3Access`

### 3b. Create IAM Role

Go to **IAM** → **Roles** → **Create role**:
1. Trusted entity type: **Custom trust policy**
2. Paste this (we'll update it later):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::000000000000:root"
      },
      "Action": "sts:AssumeRole",
      "Condition": {}
    }
  ]
}
```

3. Click **Next**, attach the `SnowflakeHealthcareS3Access` policy
4. Role name: `SnowflakeHealthcareRole`
5. Click **Create role**

> **Copy the Role ARN** (e.g., `arn:aws:iam::123456789012:role/SnowflakeHealthcareRole`)

---

## Step 4: Create Storage Integration & External Stages (Snowflake)

**Duration:** 5 minutes

Replace the placeholders and run in Snowsight:

```sql
USE ROLE ACCOUNTADMIN;
USE DATABASE HEALTHCARE_AI_DEMO;
USE WAREHOUSE HEALTHCARE_AI_WH;

-- Replace <YOUR_BUCKET_NAME> and <YOUR_AWS_IAM_ROLE_ARN>
CREATE OR REPLACE STORAGE INTEGRATION HEALTHCARE_S3_INTEGRATION
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = 'S3'
  ENABLED = TRUE
  STORAGE_AWS_ROLE_ARN = '<YOUR_AWS_IAM_ROLE_ARN>'
  STORAGE_ALLOWED_LOCATIONS = ('s3://<YOUR_BUCKET_NAME>/healthcare/');

-- Get Snowflake's IAM user ARN and external ID
DESCRIBE INTEGRATION HEALTHCARE_S3_INTEGRATION;
```

> **IMPORTANT: Copy these two values from the output:**
> - `STORAGE_AWS_IAM_USER_ARN` (e.g., `arn:aws:iam::123456789012:user/abcd0000-s`)
> - `STORAGE_AWS_EXTERNAL_ID` (e.g., `QY71556_SFCRole=3_abc123...`)

Now create the external stages:

```sql
-- Replace <YOUR_BUCKET_NAME> in all 3 stages
CREATE OR REPLACE STAGE RAW.S3_MEDICAL_DOCS
  URL = 's3://<YOUR_BUCKET_NAME>/healthcare/pdfs/'
  STORAGE_INTEGRATION = HEALTHCARE_S3_INTEGRATION
  DIRECTORY = (ENABLE = TRUE AUTO_REFRESH = TRUE);

CREATE OR REPLACE STAGE RAW.S3_MEDICAL_TXT
  URL = 's3://<YOUR_BUCKET_NAME>/healthcare/txt/'
  STORAGE_INTEGRATION = HEALTHCARE_S3_INTEGRATION
  DIRECTORY = (ENABLE = TRUE AUTO_REFRESH = TRUE);

CREATE OR REPLACE STAGE RAW.S3_MEDICAL_AUDIO
  URL = 's3://<YOUR_BUCKET_NAME>/healthcare/audio/'
  STORAGE_INTEGRATION = HEALTHCARE_S3_INTEGRATION
  DIRECTORY = (ENABLE = TRUE AUTO_REFRESH = TRUE);

CREATE OR REPLACE STAGE ANALYTICS.SEMANTIC_MODELS
  DIRECTORY = (ENABLE = TRUE);
```

---

## Step 5: Update IAM Trust Policy (AWS)

**Duration:** 3 minutes

Go back to **AWS Console** → **IAM** → **Roles** → `SnowflakeHealthcareRole` → **Trust relationships** → **Edit trust policy**:

Replace the trust policy with (using the values from Step 4):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "<STORAGE_AWS_IAM_USER_ARN from Step 4>"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "<STORAGE_AWS_EXTERNAL_ID from Step 4>"
        }
      }
    }
  ]
}
```

Click **Update policy**.

> **Wait 30 seconds** for IAM propagation, then verify in Snowflake:
```sql
LIST @RAW.S3_MEDICAL_DOCS;
-- Should return empty (no files yet) without errors
```

---

## Step 6: Create Snowpipes & Stream (Snowflake)

**Duration:** 3 minutes

```sql
USE DATABASE HEALTHCARE_AI_DEMO;
USE SCHEMA RAW;

-- Landing table for file metadata
CREATE OR REPLACE TABLE RAW.FILES_LOG (
    FILE_ID       NUMBER AUTOINCREMENT PRIMARY KEY,
    FILE_NAME     VARCHAR NOT NULL,
    FILE_PATH     VARCHAR NOT NULL,
    FILE_TYPE     VARCHAR(10) NOT NULL,
    S3_EVENT_TIME TIMESTAMP_NTZ,
    LANDED_AT     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    IS_PROCESSED  BOOLEAN DEFAULT FALSE,
    PROCESSED_AT  TIMESTAMP_NTZ
);

-- Metadata-only format (skips content parsing for binary files)
CREATE OR REPLACE FILE FORMAT RAW.METADATA_ONLY_FORMAT
  TYPE = 'CSV' RECORD_DELIMITER = NONE FIELD_DELIMITER = NONE;

-- Snowpipe for PDFs
CREATE OR REPLACE PIPE RAW.PIPE_MEDICAL_DOCS AUTO_INGEST = TRUE AS
  COPY INTO RAW.FILES_LOG (FILE_NAME, FILE_PATH, FILE_TYPE, S3_EVENT_TIME)
  FROM (
    SELECT METADATA$FILENAME, METADATA$FILENAME, 'PDF', METADATA$START_SCAN_TIME
    FROM @RAW.S3_MEDICAL_DOCS
  )
  FILE_FORMAT = (FORMAT_NAME = 'RAW.METADATA_ONLY_FORMAT');

-- Snowpipe for TXT
CREATE OR REPLACE PIPE RAW.PIPE_MEDICAL_TXT AUTO_INGEST = TRUE AS
  COPY INTO RAW.FILES_LOG (FILE_NAME, FILE_PATH, FILE_TYPE, S3_EVENT_TIME)
  FROM (
    SELECT METADATA$FILENAME, METADATA$FILENAME, 'TXT', METADATA$START_SCAN_TIME
    FROM @RAW.S3_MEDICAL_TXT
  )
  FILE_FORMAT = (FORMAT_NAME = 'RAW.METADATA_ONLY_FORMAT');

-- Snowpipe for Audio
CREATE OR REPLACE PIPE RAW.PIPE_MEDICAL_AUDIO AUTO_INGEST = TRUE AS
  COPY INTO RAW.FILES_LOG (FILE_NAME, FILE_PATH, FILE_TYPE, S3_EVENT_TIME)
  FROM (
    SELECT METADATA$FILENAME, METADATA$FILENAME,
      CASE WHEN METADATA$FILENAME ILIKE '%.mp3' THEN 'MP3' ELSE 'WAV' END,
      METADATA$START_SCAN_TIME
    FROM @RAW.S3_MEDICAL_AUDIO
  )
  FILE_FORMAT = (FORMAT_NAME = 'RAW.METADATA_ONLY_FORMAT');

-- Stream to detect new file arrivals
CREATE OR REPLACE STREAM RAW.FILES_LOG_STREAM
  ON TABLE RAW.FILES_LOG APPEND_ONLY = TRUE;

-- Get the SQS queue ARN (needed for S3 event notifications)
SHOW PIPES IN SCHEMA RAW;
```

> **Copy the `notification_channel` value** from any pipe row — this is the SQS queue ARN.
> (e.g., `arn:aws:sqs:eu-central-1:123456789012:sf-snowpipe-AIDA...`)

---

## Step 7: Configure S3 Event Notifications (AWS)

**Duration:** 5 minutes

### AWS Console

1. Go to **S3** → Your bucket → **Properties** → **Event notifications**
2. Create **3 event notifications**:

| Name | Prefix | Events | Destination |
|------|--------|--------|-------------|
| `snowpipe-pdfs` | `healthcare/pdfs/` | All object create events | SQS queue → paste the ARN from Step 6 |
| `snowpipe-txt` | `healthcare/txt/` | All object create events | SQS queue → paste the ARN from Step 6 |
| `snowpipe-audio` | `healthcare/audio/` | All object create events | SQS queue → paste the ARN from Step 6 |

---

## Step 8: Upload Sample Files & Verify Ingestion

**Duration:** 5 minutes

### Upload the sample files to S3

This repo includes 15 pre-made sample files in `sample_files/`. Upload them to your S3 bucket using the AWS CLI:

```bash
BUCKET_NAME="healthcare-ai-demo-<your-initials>"

# Upload PDFs (6 files)
aws s3 cp sample_files/clinical_notes_obrien.pdf s3://$BUCKET_NAME/healthcare/pdfs/
aws s3 cp sample_files/discharge_summary_whitfield.pdf s3://$BUCKET_NAME/healthcare/pdfs/
aws s3 cp sample_files/insurance_claim_brown.pdf s3://$BUCKET_NAME/healthcare/pdfs/
aws s3 cp sample_files/lab_report_sullivan.pdf s3://$BUCKET_NAME/healthcare/pdfs/
aws s3 cp sample_files/prescription_garcia.pdf s3://$BUCKET_NAME/healthcare/pdfs/
aws s3 cp sample_files/radiology_report_park.pdf s3://$BUCKET_NAME/healthcare/pdfs/

# Upload TXT files (4 files)
aws s3 cp sample_files/nurse_notes_anderson.txt s3://$BUCKET_NAME/healthcare/txt/
aws s3 cp sample_files/pathology_report_lee.txt s3://$BUCKET_NAME/healthcare/txt/
aws s3 cp sample_files/patient_intake_torres.txt s3://$BUCKET_NAME/healthcare/txt/
aws s3 cp sample_files/referral_letter_zhang.txt s3://$BUCKET_NAME/healthcare/txt/

# Upload Audio files (5 files)
aws s3 cp sample_files/consultation_garcia_cardiac.wav s3://$BUCKET_NAME/healthcare/audio/
aws s3 cp sample_files/consultation_johnson_pediatric.mp3 s3://$BUCKET_NAME/healthcare/audio/
aws s3 cp sample_files/consultation_obrien_therapy.wav s3://$BUCKET_NAME/healthcare/audio/
aws s3 cp sample_files/consultation_tanaka_dermatology.mp3 s3://$BUCKET_NAME/healthcare/audio/
aws s3 cp sample_files/consultation_whitfield_bp.wav s3://$BUCKET_NAME/healthcare/audio/
```

Or upload all at once:
```bash
aws s3 cp sample_files/ s3://$BUCKET_NAME/healthcare/ --recursive --exclude "*" \
  --include "*.pdf" --include "*.txt" --include "*.wav" --include "*.mp3"
```

> **Alternative (no AWS CLI):** You can also upload files via the AWS Console: S3 → your bucket → navigate to the correct prefix folder → Upload.

### Trigger ingestion

In Snowflake:
```sql
-- Manual refresh to pick up existing files
ALTER PIPE RAW.PIPE_MEDICAL_DOCS REFRESH;
ALTER PIPE RAW.PIPE_MEDICAL_TXT REFRESH;
ALTER PIPE RAW.PIPE_MEDICAL_AUDIO REFRESH;

-- Wait 1-2 minutes, then verify:
SELECT FILE_TYPE, COUNT(*) AS FILES
FROM HEALTHCARE_AI_DEMO.RAW.FILES_LOG
GROUP BY FILE_TYPE;
```

Expected:
| FILE_TYPE | FILES |
|-----------|-------|
| PDF | 6 |
| TXT | 4 |
| WAV | 5 |

> **Important:** The FILE_NAME column stores the path relative to the bucket root (e.g., `healthcare/pdfs/file.pdf`). The processing procedures need just the filename. Fix this:

```sql
UPDATE HEALTHCARE_AI_DEMO.RAW.FILES_LOG
SET FILE_NAME = REGEXP_REPLACE(FILE_NAME, '^healthcare/(pdfs|txt|audio)/', '')
WHERE FILE_NAME LIKE 'healthcare/%';
```

---

## Step 9: Create AI Processing Tables

**Duration:** 2 minutes

Run `assets/04_processing_tables.sql` or copy-paste from the file in this repo. This creates:
- `PROCESSED.PDF_INTELLIGENCE` (15 columns of AI-enriched data)
- `PROCESSED.TXT_INTELLIGENCE` (14 columns)
- `PROCESSED.AUDIO_INTELLIGENCE` (17 columns)

---

## Step 10: Create & Run AI Processing Procedures

**Duration:** 15 minutes (AI processing takes time)

Run scripts `assets/05_proc_pdf.sql`, `assets/06_proc_txt.sql`, `assets/07_proc_audio.sql`.

> **Regional note:** If `claude-3-5-sonnet` is unavailable, replace it with `mistral-large2` in all three scripts.

Then process the files:

```sql
CALL PROCESSED.PROCESS_PDF_FILES();
CALL PROCESSED.PROCESS_TXT_FILES();
CALL PROCESSED.PROCESS_AUDIO_FILES();
```

Verify:
```sql
SELECT 'PDF' AS TYPE, COUNT(*) AS CNT FROM PROCESSED.PDF_INTELLIGENCE
UNION ALL SELECT 'TXT', COUNT(*) FROM PROCESSED.TXT_INTELLIGENCE
UNION ALL SELECT 'AUDIO', COUNT(*) FROM PROCESSED.AUDIO_INTELLIGENCE;
```

Expected: 6 PDFs, 4 TXT, 5 Audio.

---

## Step 11: Create Cortex Search Services

**Duration:** 5 minutes

Run `assets/11_cortex_search.sql`. This creates 3 search services:
- `PROCESSED.PDF_SEARCH`
- `PROCESSED.TXT_SEARCH`
- `PROCESSED.AUDIO_SEARCH`

Verify:
```sql
SHOW CORTEX SEARCH SERVICES IN DATABASE HEALTHCARE_AI_DEMO;
```

> Wait 2-3 minutes for indexing to complete before testing.

---

## Step 12: Load Structured Data & Create Semantic View

**Duration:** 5 minutes

1. Run `assets/09_structured_data.sql` — loads Providers (12), Patients (15), Claims (30), Appointments (24)
2. Run `assets/12_semantic_view.sql` — creates the Semantic View for Cortex Analyst

Verify:
```sql
DESCRIBE SEMANTIC VIEW ANALYTICS.HEALTHCARE_ANALYTICS;
```

---

## Step 13: Create the Cortex Agent

**Duration:** 3 minutes

Run `assets/13_cortex_agent.sql`. This creates:
- `ANALYTICS.HEALTHCARE_INTELLIGENCE_AGENT` with 4 tools:
  - **HealthcareAnalyst** (Cortex Analyst over Semantic View)
  - **PDFSearch** (Cortex Search over PDFs)
  - **TXTSearch** (Cortex Search over TXT)
  - **AudioSearch** (Cortex Search over audio transcripts)

Verify:
```sql
DESCRIBE AGENT ANALYTICS.HEALTHCARE_INTELLIGENCE_AGENT;
```

---

## Step 14: Test via Snowflake Intelligence

**Duration:** 10 minutes

1. In Snowsight, go to **AI & ML** → **Intelligence**
2. Click **+ New** or **Create**
3. Set Agent to `HEALTHCARE_AI_DEMO.ANALYTICS.HEALTHCARE_INTELLIGENCE_AGENT`
4. Click **Create**

### Test Questions

**Structured data (Cortex Analyst):**
- "Which providers have the highest total billed amounts?"
- "How many claims were denied and what were the reasons?"
- "What is the average claim amount by specialty?"

**Unstructured search (Cortex Search):**
- "Find documents mentioning diabetes or hypertension"
- "What consultations discussed medication changes?"
- "Search for post-operative nursing observations"

**Cross-tool (Agent orchestration):**
- "What are the most common diagnoses across all medical documents?"
- "Compare findings across PDF and text documents"

---

## Step 15: Set Up Automated Processing (Optional)

**Duration:** 2 minutes

Create a stream-triggered task that automatically processes new files:

```sql
CREATE OR REPLACE PROCEDURE PROCESSED.PROCESS_NEW_FILES()
  RETURNS VARCHAR LANGUAGE SQL EXECUTE AS CALLER
AS $$
BEGIN
  CALL PROCESSED.PROCESS_PDF_FILES();
  CALL PROCESSED.PROCESS_TXT_FILES();
  CALL PROCESSED.PROCESS_AUDIO_FILES();
  RETURN 'Processing complete: ' || CURRENT_TIMESTAMP()::VARCHAR;
END; $$;

CREATE OR REPLACE TASK RAW.PROCESS_NEW_FILES_TASK
  WAREHOUSE = HEALTHCARE_AI_WH
  SCHEDULE = '1 MINUTE'
  WHEN SYSTEM$STREAM_HAS_DATA('RAW.FILES_LOG_STREAM')
AS CALL PROCESSED.PROCESS_NEW_FILES();

ALTER TASK RAW.PROCESS_NEW_FILES_TASK RESUME;
```

Now any new file uploaded to S3 will be automatically processed within ~2 minutes.

---

## Cleanup

```sql
ALTER TASK HEALTHCARE_AI_DEMO.RAW.PROCESS_NEW_FILES_TASK SUSPEND;
DROP DATABASE IF EXISTS HEALTHCARE_AI_DEMO;
DROP WAREHOUSE IF EXISTS HEALTHCARE_AI_WH;
DROP STORAGE INTEGRATION IF EXISTS HEALTHCARE_S3_INTEGRATION;
```

AWS:
```bash
aws s3 rb s3://<YOUR_BUCKET_NAME> --force
aws iam detach-role-policy --role-name SnowflakeHealthcareRole \
  --policy-arn arn:aws:iam::<ACCOUNT>:policy/SnowflakeHealthcareS3Access
aws iam delete-role --role-name SnowflakeHealthcareRole
aws iam delete-policy --policy-arn arn:aws:iam::<ACCOUNT>:policy/SnowflakeHealthcareS3Access
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| FILES_LOG is empty after upload | Check S3 event notifications point to correct SQS ARN. Try `ALTER PIPE ... REFRESH;` |
| "Access Denied" on stage | Verify IAM trust policy has correct `STORAGE_AWS_IAM_USER_ARN` and `STORAGE_AWS_EXTERNAL_ID` from `DESCRIBE INTEGRATION` |
| `claude-3-5-sonnet` unavailable | Replace with `mistral-large2` or `llama3.3-70b` in proc scripts |
| AI_PARSE_DOCUMENT "file not found" | FILE_NAME may include prefix. Run the `REGEXP_REPLACE` UPDATE from Step 8 |
| Cortex Search "no results" | Wait 2-3 minutes for indexing after creating the service |

---

## Resources

- [Official Quickstart](https://www.snowflake.com/en/developers/guides/aws-s3-data-intelligence-with-cortex-ai-functions-search-analyst-and-agents/)
- [Cortex AI Functions](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-ai)
- [Cortex Search](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search)
- [Cortex Analyst](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)
- [Cortex Agent](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agent)
- [Snowpipe Auto-Ingest with S3](https://docs.snowflake.com/en/user-guide/data-load-snowpipe-auto-s3)
