# AWS Setup Guide — Step by Step

This guide walks you through the AWS Console steps needed before running the lab notebook. Complete these steps first, then return to the notebook.

---

## Step 0: Create a Snowflake Free Trial Account

1. Go to [snowflake.com/en/data-cloud/platform/trial](https://signup.snowflake.com/)
2. Fill in your name, email, and company
3. Choose:
   - **Cloud Provider:** AWS
   - **Region:** EU (Frankfurt) — `eu-central-1`
   - **Edition:** Enterprise (required for Cortex AI features)
4. Click **Get Started**
5. Check your email and click the activation link
6. Set your username and password

> **Important:** Select **AWS eu-central-1** so that your Snowflake account is in the same region as your S3 bucket. This avoids cross-region data transfer fees.

Once logged in, you are automatically ACCOUNTADMIN — the role needed for this lab.

### Enable Cross-Region Cortex AI (recommended)

In a Snowsight worksheet, run:

```sql
ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION';
```

This ensures all Cortex AI models are available regardless of your account region.

---

## Step A: Create an S3 Bucket

> **No AWS account?** Create one at [aws.amazon.com/free](https://aws.amazon.com/free/). The free tier includes 5 GB of S3 storage — more than enough for this lab. You'll need a credit card for verification but won't be charged.

1. Go to [AWS Console](https://console.aws.amazon.com/) and sign in
2. Search for **S3** in the top search bar and click it
3. Click the orange **Create bucket** button
4. Fill in:
   - **Bucket name:** `healthcare-ai-demo-<your-initials>` (e.g., `healthcare-ai-demo-jsmith`)
   - **AWS Region:** Select `eu-central-1 (Frankfurt)` (or the same region as your Snowflake account)
   - Leave all other settings as default
5. Click **Create bucket** at the bottom

### Create the folder structure:

6. Click on your new bucket name to open it
7. Click **Create folder**
8. Folder name: `healthcare` → click **Create folder**
9. Click into the `healthcare` folder
10. Click **Create folder** → name it `pdfs` → click **Create folder**

Your bucket should now have the path: `s3://your-bucket-name/healthcare/pdfs/`

### Upload sample files:

11. Navigate into the `healthcare/pdfs/` folder
12. Click **Upload**
13. Click **Add files** and select all 6 PDF files from the `sample_files/` folder in this repo
14. Click **Upload**

---

## Step B: Create an IAM Policy

1. In the AWS Console, search for **IAM** and click it
2. In the left sidebar, click **Policies**
3. Click **Create policy**
4. Click the **JSON** tab (top right of the policy editor)
5. Delete the default content and paste this (replace `<YOUR_BUCKET_NAME>` with your actual bucket name):

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

6. Click **Next**
7. Policy name: `SnowflakeHealthcareS3Access`
8. Click **Create policy**

---

## Step C: Create an IAM Role

1. In IAM, click **Roles** in the left sidebar
2. Click **Create role**
3. For "Trusted entity type," select **Custom trust policy**
4. In the JSON editor, paste this temporary trust policy:

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

5. Click **Next**
6. Search for `SnowflakeHealthcareS3Access` and check the box next to it
7. Click **Next**
8. Role name: `SnowflakeHealthcareRole`
9. Click **Create role**

### Copy the Role ARN:

10. Click on the role you just created
11. At the top, you'll see **ARN** — copy it (looks like `arn:aws:iam::123456789012:role/SnowflakeHealthcareRole`)
12. **Save this ARN** — you'll need it in the notebook (Step 2)

---

## Step D: Update Trust Policy (after running notebook Step 2)

After running the `DESCRIBE INTEGRATION` cell in the notebook, you'll get two values:
- `STORAGE_AWS_IAM_USER_ARN`
- `STORAGE_AWS_EXTERNAL_ID`

Now update the trust policy:

1. Go to **IAM → Roles → SnowflakeHealthcareRole**
2. Click the **Trust relationships** tab
3. Click **Edit trust policy**
4. Replace the ENTIRE JSON with:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "<paste STORAGE_AWS_IAM_USER_ARN here>"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "<paste STORAGE_AWS_EXTERNAL_ID here>"
        }
      }
    }
  ]
}
```

5. Click **Update policy**
6. **Wait 30 seconds** — AWS needs time to propagate the change
7. Return to the notebook and continue

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| "Access Denied" when creating stage | Your trust policy values don't match. Re-run `DESCRIBE INTEGRATION` and compare with what's in your trust policy |
| Bucket region mismatch | Ensure your S3 bucket is in the same region as your Snowflake account |
| "Bucket already exists" | Bucket names are globally unique. Add your initials or a number |
| Can't find the role | Make sure you're in the correct AWS account |
| Policy not attaching | Search for the exact name `SnowflakeHealthcareS3Access` |

---

## What you need for the notebook

After completing these steps, you should have:
- [ ] S3 bucket name (e.g., `healthcare-ai-demo-jsmith`)
- [ ] IAM Role ARN (e.g., `arn:aws:iam::123456789012:role/SnowflakeHealthcareRole`)
- [ ] 6 PDF files uploaded to `s3://your-bucket/healthcare/pdfs/`

Open the notebook and enter these values in Step 2.
