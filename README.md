![S3 Data Intelligence Lab](banner.svg)

# AWS + Snowflake Hands-On Lab: S3 Data Intelligence with Cortex AI

60-minute lab: S3 → Cortex AI Functions → Cortex Search → Cortex Analyst → Cortex Agent → Snowflake Intelligence.

Healthcare PDF documents are ingested from S3, processed through Cortex AI functions (parse, extract, classify, summarize, redact, sentiment, translate, embed), then exposed via a unified Cortex Agent that combines structured queries (Cortex Analyst) with semantic document search (Cortex Search).

## Architecture

```
S3 Bucket (PDFs)
       │
  Storage Integration + External Stage
       │
  DIRECTORY() → INSERT...SELECT with AI functions
       │
  PDF_INTELLIGENCE table
       │
  ┌─────────────────────────────────────┐
  │  Cortex Search (semantic retrieval) │
  │  Cortex Analyst (Semantic View)     │
  │  Cortex Agent (combined tools)      │
  │  Streamlit Chat App                 │
  │  Snowflake Intelligence (chat UI)   │
  └─────────────────────────────────────┘
```

## How to Run

1. Complete the AWS setup: **[AWS_SETUP_GUIDE.md](AWS_SETUP_GUIDE.md)**
2. Import **[lab_notebook.ipynb](lab_notebook.ipynb)** into Snowsight (Projects → Notebooks)
3. Run cells sequentially — everything is self-contained

## Prerequisites

- Snowflake account with ACCOUNTADMIN role and Cortex AI enabled
- AWS account with permissions to create S3 buckets and IAM roles
- ~60 minutes

## Repo Contents

| File | Description |
|------|-------------|
| `lab_notebook.ipynb` | Self-contained 9-step lab notebook (run in Snowsight) |
| `AWS_SETUP_GUIDE.md` | Click-by-click AWS Console companion guide |
| `sample_files/` | 6 sample healthcare PDFs to upload to S3 |
| `banner.svg` | Repo banner |

## What You'll Build

1. **Cortex AI Processing Pipeline** — Parse, extract, classify, summarize, redact, translate, embed PDFs
2. **Cortex Search Service** — Semantic search over processed documents
3. **Cortex Agent** — Unified agent combining structured + unstructured queries
4. **Streamlit Chat App** — Deployed chat interface
5. **Snowflake Intelligence** — Native chat UI for the agent

## Cleanup

```sql
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
