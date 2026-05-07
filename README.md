# S3 Data Intelligence Lab with Snowflake Cortex

Complete pipeline: S3 file ingestion -> Cortex AI functions (11) -> Cortex Search -> Cortex Analyst -> Cortex Agent -> Snowflake Intelligence.

Healthcare documents (PDFs, TXT, audio) are auto-ingested from S3 via Snowpipe, processed through 11 Cortex AI functions, then exposed via a unified agent that combines structured queries (Cortex Analyst) with semantic search (Cortex Search).

## Architecture

```
S3 Bucket (pdfs/, txt/, audio/)
        |
  S3 Event Notification -> SQS (Snowflake-managed)
        |
  Snowpipe (x3) -> FILES_LOG -> Stream -> Task
        |
  Stored Procedures (one per file type)
  applying 9-10 Cortex AI functions each
        |
  Intelligence Tables (PDF, TXT, Audio)
        |
  +-------------------------------------+
  |  Cortex Search (3 services)         |
  |  Cortex Analyst (Semantic View)     |
  |  Cortex Agent (4 tools)             |
  |  Snowflake Intelligence (chat UI)   |
  +-------------------------------------+
```

## Prerequisites

- Snowflake account with ACCOUNTADMIN role and Cortex AI functions enabled
- AWS account with S3 access (SE-Sandbox or equivalent)
- Cross-region inference enabled (`CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION'`)
- Python 3.10+ with `boto3` (for sample file generation)

## Regional Adaptation

The official quickstart uses `claude-3-5-sonnet` for AI_COMPLETE. If this model is unavailable in your region, replace it with `mistral-large2` or `llama3.3-70b` in scripts `05_proc_pdf.sql`, `06_proc_txt.sql`, and `07_proc_audio.sql`.

## Quick Setup (Step by Step)

### Step 1: AWS Setup

1. Create an S3 bucket in the same region as your Snowflake account:
   ```
   Bucket: <your-bucket-name>
   Region: eu-central-1 (or matching your SF region)
   Prefixes: healthcare/pdfs/, healthcare/txt/, healthcare/audio/
   ```

2. Create an IAM policy with S3 read access to your bucket.

3. Create an IAM role (`SnowflakeS3IntelligenceLab`) with a placeholder trust policy.

### Step 2: Snowflake Infrastructure

Run scripts in order:
```sql
-- 1. Database, schemas, warehouse
-- Edit 02_s3_integration_and_stages.sql with your bucket name and IAM role ARN
01_database_and_schemas.sql
02_s3_integration_and_stages.sql   -- REPLACE placeholders!
```

After running script 02, get Snowflake's IAM user ARN and external ID:
```sql
DESCRIBE INTEGRATION HEALTHCARE_S3_INTEGRATION;
```
Update your IAM role trust policy with those values (see `14_aws_setup_guide.sql`).

### Step 3: File Ingestion

```sql
03_file_ingestion.sql   -- Creates pipes, stream
-- Get SQS ARN from SHOW PIPES and configure S3 event notifications
```

### Step 4: Upload Sample Files

```bash
python generate_sample_data.py   -- Generates and uploads healthcare sample files
```

### Step 5: AI Processing Pipeline

```sql
04_processing_tables.sql
05_proc_pdf.sql          -- NOTE: replace claude-3-5-sonnet with mistral-large2 if needed
06_proc_txt.sql
07_proc_audio.sql
08_orchestrator_proc_and_task.sql
```

Run processing manually or wait for the stream-triggered task:
```sql
CALL PROCESSED.PROCESS_NEW_FILES();
```

### Step 6: Cortex Search + Analyst + Agent

```sql
09_structured_data.sql   -- Sample healthcare tables
10_analytics_views.sql   -- Optional analytics views
11_cortex_search.sql     -- 3 search services
12_semantic_view.sql     -- Semantic view for Cortex Analyst
13_cortex_agent.sql      -- Agent combining all tools
```

### Step 7: Snowflake Intelligence

1. Navigate to **AI & ML > Intelligence** in Snowsight
2. Click **New Agent**
3. Select `HEALTHCARE_AI_DEMO.ANALYTICS.HEALTHCARE_INTELLIGENCE_AGENT`
4. The 4 tools are inherited automatically

## Demo Talking Points

1. **End-to-end AI pipeline**: Files land in S3, get auto-ingested, enriched with 11 AI functions, and become searchable
2. **11 Cortex AI functions**: Parse, Transcribe, Extract, Classify, Sentiment, Summarize, Translate, Redact, Complete, Embed
3. **No data leaves Snowflake**: Files stay in S3, accessed via external stages with IAM trust
4. **Unified agent**: Single conversational interface over structured + unstructured data
5. **Event-driven**: Stream-triggered task automatically processes new files within 1 minute

## Files

| File | Description |
|------|-------------|
| `assets/01-16_*.sql` | Official quickstart SQL scripts (16 total) |
| `generate_sample_data.py` | Python script to generate sample healthcare files |
| `README.md` | This file |

## Cleanup

```sql
ALTER TASK HEALTHCARE_AI_DEMO.RAW.PROCESS_NEW_FILES_TASK SUSPEND;
DROP DATABASE IF EXISTS HEALTHCARE_AI_DEMO;
DROP WAREHOUSE IF EXISTS HEALTHCARE_AI_WH;
DROP STORAGE INTEGRATION IF EXISTS HEALTHCARE_S3_INTEGRATION;
```

## Resources

- [Official Quickstart](https://www.snowflake.com/en/developers/guides/aws-s3-data-intelligence-with-cortex-ai-functions-search-analyst-and-agents/)
- [Cortex AI Functions](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-ai)
- [Cortex Search](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search)
- [Cortex Analyst](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)
- [Cortex Agent](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agent)
