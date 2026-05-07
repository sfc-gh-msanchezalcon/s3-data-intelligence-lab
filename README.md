# AWS S3 Data Intelligence with Cortex AI Functions, Search, Analyst & Agents

Hands-on lab: S3 file ingestion → 11 Cortex AI functions → Cortex Search → Cortex Analyst → Cortex Agent → Snowflake Intelligence.

Healthcare documents (PDFs, TXT, audio) are auto-ingested from S3 via Snowpipe, processed through 11 Cortex AI functions, then exposed via a unified agent that combines structured queries (Cortex Analyst) with semantic search (Cortex Search).

## Architecture

```
S3 Bucket (pdfs/, txt/, audio/)
        |
  S3 Event Notification → SQS (Snowflake-managed)
        |
  Snowpipe (x3) → FILES_LOG → Stream → Task
        |
  Stored Procedures (one per file type)
  applying 9-10 Cortex AI functions each
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

## How to Run This Lab

Follow **[LAB_GUIDE.md](LAB_GUIDE.md)** — a step-by-step quickstart guide (15 steps) with all SQL and AWS instructions.

Alternatively, import **[lab_notebook.ipynb](lab_notebook.ipynb)** into Snowsight (Projects → Notebooks) and run cells sequentially.

## Prerequisites

- Snowflake account with ACCOUNTADMIN role and Cortex AI functions enabled
- AWS account with permissions to create S3 buckets, IAM roles, and event notifications
- AWS CLI installed (or use AWS Console for all AWS steps)

## Regional Note

The official quickstart uses `claude-3-5-sonnet` for AI_COMPLETE. If unavailable in your region, replace with `mistral-large2` or `llama3.3-70b` in scripts `05_proc_pdf.sql`, `06_proc_txt.sql`, and `07_proc_audio.sql`.

Ensure cross-region inference is enabled:
```sql
SHOW PARAMETERS LIKE 'CORTEX_ENABLED_CROSS_REGION' IN ACCOUNT;
```

## Repo Contents

| File/Folder | Description |
|-------------|-------------|
| `LAB_GUIDE.md` | Full step-by-step lab guide (quickstart format) |
| `lab_notebook.ipynb` | Snowflake Notebook — run the lab cell-by-cell in Snowsight |
| `assets/01-16_*.sql` | Official quickstart SQL scripts (16 total) |
| `sample_files/` | Pre-made sample healthcare files (6 PDFs, 4 TXT, 5 audio) |
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
- [Snowpipe Auto-Ingest with S3](https://docs.snowflake.com/en/user-guide/data-load-snowpipe-auto-s3)
