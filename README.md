# EC2 Snapshot Cleanup Lambda

Automated AWS Lambda function that deletes EC2 snapshots older than a specified retention period (default: 365 days).

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          AWS Account / Region                        │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    VPC (10.0.0.0/16)                           │ │
│  │                                                                 │ │
│  │  ┌──────────────────────────────────────────────────────────┐ │ │
│  │  │         Private Subnet (10.0.1.0/24)                     │ │ │
│  │  │                                                           │ │ │
│  │  │  ┌─────────────────────────────────────────┐            │ │ │
│  │  │  │  Lambda Function                        │            │ │ │
│  │  │  │  - snapshot-cleanup                     │            │ │ │
│  │  │  │  - Python 3.11                          │            │ │ │
│  │  │  │  - 256MB / 5min timeout                 │            │ │ │
│  │  │  └──────────────┬──────────────────────────┘            │ │ │
│  │  │                 │                                        │ │ │
│  │  │                 │ Uses                                   │ │ │
│  │  │                 ▼                                        │ │ │
│  │  │  ┌─────────────────────────────────────────┐            │ │ │
│  │  │  │  Security Group                         │            │ │ │
│  │  │  │  - Egress: HTTPS (443)                  │            │ │ │
│  │  │  └─────────────────────────────────────────┘            │ │ │
│  │  │                                                           │ │ │
│  │  └───────────────────────────────────────────────────────────┘ │ │
│  │                                                                 │ │
│  │  ┌──────────────────────────────────────────────────────────┐ │ │
│  │  │  VPC Endpoints (Interface)                               │ │ │
│  │  │  - com.amazonaws.region.ec2                              │ │ │
│  │  │  - com.amazonaws.region.logs                             │ │ │
│  │  └──────────────────────────────────────────────────────────┘ │ │
│  │                                                                 │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  IAM Role: snapshot-cleanup-lambda-role                         │ │
│  │  Permissions:                                                    │ │
│  │  - ec2:DescribeSnapshots                                        │ │
│  │  - ec2:DeleteSnapshot                                           │ │
│  │  - logs:CreateLogGroup/CreateLogStream/PutLogEvents             │ │
│  │  - VPC execution permissions                                    │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  EventBridge Rule                                               │ │
│  │  Schedule: cron(0 2 * * ? *)  [Daily at 2 AM UTC]              │ │
│  │  Target: Lambda Function                                        │ │
│  └──────────────────────┬──────────────────────────────────────────┘ │
│                         │ Triggers                                   │
│                         ▼                                            │
│                    Lambda Execution                                  │
│                         │                                            │
│                         ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  CloudWatch Logs                                                │ │
│  │  Log Group: /aws/lambda/prod-snapshot-cleanup                   │ │
│  │  Retention: 30 days                                             │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  EC2 Snapshots                                                  │ │
│  │  - Scanned by Lambda                                            │ │
│  │  - Deleted if > 365 days old                                    │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  S3 Bucket (Lambda Artifacts)                                   │ │
│  │  - Stores Lambda deployment package (.zip)                      │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

## IaC Tool Choice

**Tool: AWS CloudFormation**

**Why CloudFormation:**
- Native AWS service with no additional tooling required
- Built-in drift detection and rollback capabilities
- Direct integration with AWS services
- Stack exports/imports for modular infrastructure
- No state file management (unlike Terraform)
- Enterprise-standard for AWS deployments
- Better suited for AWS-only infrastructure

**Architecture:**
- Two separate CloudFormation stacks:
  - `infra.yaml`: Infrastructure (VPC, networking, IAM)
  - `app.yaml`: Application (Lambda, EventBridge, CloudWatch)
- Separation allows independent updates to infrastructure vs application code

## Configuration Management

**This project uses `config.json` for environment-specific configuration.**

**Why config.json:**
- Version controlled with code
- Easy to review changes in PRs
- No AWS API calls needed during deployment
- Simple to use with `jq` in CodeBuild
- Transparent and self-documenting

**Configuration file:** `config/prod.json`
```json
{
  "environment": "prod",
  "retention_days": 365,
  "cron_schedule": "cron(0 2 * * ? *)",
  "s3_bucket": "your-lambda-artifacts-bucket",
  "vpc_cidr": "10.0.0.0/16",
  "subnet_cidr": "10.0.1.0/24"
}
```

**To modify configuration:**
1. Edit `config/prod.json`
2. Commit and push changes
3. CodeBuild pipeline will use new values automatically

## Required IAM Roles

**The deployment requires the following IAM roles with appropriate permissions:**

### 1. CodeBuild Service Role

**Required permissions:**
- CloudFormation: `cloudformation:*`
- EC2: `ec2:*` (for VPC resources)
- IAM: `iam:*` (for creating Lambda execution role)
- Lambda: `lambda:*`
- S3: `s3:PutObject`, `s3:GetObject`
- Logs: `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`
- Events: `events:*` (for EventBridge rules)

**Trust relationship:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "codebuild.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

### 2. CodePipeline Service Role (if using CodePipeline)

**Required permissions:**
- CodeBuild: `codebuild:StartBuild`, `codebuild:BatchGetBuilds`
- S3: `s3:GetObject`, `s3:PutObject` (for artifacts)
- CodeCommit/GitHub: Source repository access

**Trust relationship:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "codepipeline.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

### 3. Lambda Execution Role (created by infra.yaml)

**This role is automatically created by the infrastructure CloudFormation template.**

**Permissions:**
- EC2: `ec2:DescribeSnapshots`, `ec2:DeleteSnapshot`
- Logs: `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`
- VPC: `ec2:CreateNetworkInterface`, `ec2:DescribeNetworkInterfaces`, `ec2:DeleteNetworkInterface`

### Account Access

**All roles need access to the deployment AWS account:**
- CodeBuild role deploys CloudFormation stacks in the target account
- CodePipeline role orchestrates the deployment
- Lambda execution role runs in the target account
- All resources (VPC, Lambda, EventBridge) are created in the same account

**For cross-account deployments:**
- Create assume role in target account
- Grant CodeBuild/CodePipeline permission to assume that role
- Use `--role-arn` in CloudFormation deploy commands

## Prerequisites

1. AWS CLI installed and configured
2. AWS account with appropriate permissions
3. **IAM roles created** (CodeBuild and optionally CodePipeline)
4. S3 bucket for Lambda artifacts (update in `config/prod.json`):
   ```bash
   aws s3 mb s3://your-lambda-artifacts-bucket
   ```

## Deployment Instructions

### Step 1: Deploy Infrastructure Stack

Deploy VPC, subnets, security groups, VPC endpoints, and IAM role:

```bash
aws cloudformation create-stack \
  --stack-name snapshot-cleanup-infra \
  --template-body file://infra/infra.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameters \
    ParameterKey=Environment,ParameterValue=prod \
    ParameterKey=VpcCidr,ParameterValue=10.0.0.0/16 \
    ParameterKey=PrivateSubnetCidr,ParameterValue=10.0.1.0/24
```

Wait for stack creation to complete:
```bash
aws cloudformation wait stack-create-complete \
  --stack-name snapshot-cleanup-infra
```

Verify stack outputs:
```bash
aws cloudformation describe-stacks \
  --stack-name snapshot-cleanup-infra \
  --query 'Stacks[0].Outputs'
```

### Step 2: Package Lambda Function

Navigate to Lambda directory and package the code:

```bash
cd app/lambda
pip install -r requirements.txt -t .
zip -r ../../lambda-function.zip .
cd ../..
```

### Step 3: Upload Lambda Package to S3

```bash
aws s3 cp lambda-function.zip \
  s3://your-lambda-artifacts-bucket/snapshot-cleanup/lambda-function.zip
```

### Step 4: Deploy Application Stack

Deploy Lambda function, EventBridge rule, and CloudWatch log group:

```bash
aws cloudformation create-stack \
  --stack-name snapshot-cleanup-app \
  --template-body file://app/app.yaml \
  --parameters \
    ParameterKey=Environment,ParameterValue=prod \
    ParameterKey=LambdaS3Bucket,ParameterValue=your-lambda-artifacts-bucket \
    ParameterKey=LambdaS3Key,ParameterValue=snapshot-cleanup/lambda-function.zip \
    ParameterKey=SnapshotRetentionDays,ParameterValue=365 \
    ParameterKey=ScheduleExpression,ParameterValue='cron(0 2 * * ? *)'
```

Wait for completion:
```bash
aws cloudformation wait stack-create-complete \
  --stack-name snapshot-cleanup-app
```

## VPC Configuration

The Lambda function is automatically configured to run within the VPC through CloudFormation:

**VPC Configuration (in app.yaml):**
```yaml
VpcConfig:
  SubnetIds:
    - !ImportValue prod-snapshot-cleanup-private-subnet-id
  SecurityGroupIds:
    - !ImportValue prod-snapshot-cleanup-lambda-sg-id
```

**How it works:**
1. Infrastructure stack exports subnet and security group IDs
2. Application stack imports these values automatically
3. Lambda is deployed with VPC configuration applied
4. No manual configuration needed

**To verify VPC configuration:**
```bash
aws lambda get-function-configuration \
  --function-name prod-snapshot-cleanup \
  --query 'VpcConfig'
```

## Updating Lambda Code

When Lambda code changes:

```bash
# Package new code
cd app/lambda
zip -r ../../lambda-function.zip .
cd ../..

# Upload to S3 (use commit ID for versioning)
COMMIT_ID=$(git rev-parse --short HEAD)
aws s3 cp lambda-function.zip \
  s3://your-lambda-artifacts-bucket/snapshot-cleanup/lambda-function-${COMMIT_ID}.zip

# Update CloudFormation stack
aws cloudformation update-stack \
  --stack-name snapshot-cleanup-app \
  --use-previous-template \
  --parameters \
    ParameterKey=Environment,UsePreviousValue=true \
    ParameterKey=LambdaS3Bucket,UsePreviousValue=true \
    ParameterKey=LambdaS3Key,ParameterValue=snapshot-cleanup/lambda-function-${COMMIT_ID}.zip \
    ParameterKey=SnapshotRetentionDays,UsePreviousValue=true \
    ParameterKey=ScheduleExpression,UsePreviousValue=true
```

## Assumptions

1. **AWS Region**: Deployment assumes `us-east-1` (configurable via AWS CLI profile/region)
2. **Single Account**: Lambda only scans/deletes snapshots owned by the deployment account
3. **Single Region**: Only processes snapshots in the deployed region
4. **Retention Period**: Default 365 days (1 year), configurable via parameter
5. **Schedule**: Daily execution at 2 AM UTC, configurable via cron expression
6. **Network**: VPC endpoints used instead of NAT Gateway (enterprise best practice)
7. **Snapshot Ownership**: Only processes snapshots with `OwnerIds=['self']`
8. **Error Handling**: Individual snapshot deletion failures don't stop execution
9. **S3 Bucket**: Pre-existing S3 bucket for Lambda artifacts
10. **Permissions**: Deployment user has full CloudFormation, EC2, IAM, Lambda, and S3 permissions

## Monitoring

### CloudWatch Logs

**Log Group**: `/aws/lambda/prod-snapshot-cleanup`

View logs:
```bash
aws logs tail /aws/lambda/prod-snapshot-cleanup --follow
```

**Log Contents:**
- Snapshot cleanup start time and retention period
- Each snapshot deletion action with snapshot ID and creation date
- Individual deletion errors (snapshot in use, permission denied, etc.)
- Summary: total deleted and error counts
- Fatal errors if Lambda execution fails

**Example Log Output:**
```
START RequestId: abc-123-def-456
Starting snapshot cleanup. Retention: 365 days. Cutoff date: 2024-01-15 14:30:45
Deleting snapshot: snap-0123456789abcdef0 (Created: 2023-06-15 10:30:00)
Deleting snapshot: snap-0abcdef123456789a (Created: 2022-03-10 08:15:00)
Error deleting snapshot snap-0fedcba987654321f: Snapshot in use by AMI
Cleanup complete. Deleted: 2, Errors: 1
END RequestId: abc-123-def-456
REPORT RequestId: abc-123-def-456 Duration: 1234.56 ms Billed Duration: 1235 ms
```

### CloudWatch Metrics

**Built-in Lambda Metrics:**
- `Invocations`: Number of times Lambda was triggered
- `Duration`: Execution time per invocation
- `Errors`: Number of failed executions
- `Throttles`: Number of throttled invocations
- `ConcurrentExecutions`: Number of concurrent executions

View metrics:
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=prod-snapshot-cleanup \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-31T23:59:59Z \
  --period 86400 \
  --statistics Sum
```

### CloudWatch Alarms (Optional)

Create alarm for Lambda errors:
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name snapshot-cleanup-errors \
  --alarm-description "Alert on Lambda execution errors" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --dimensions Name=FunctionName,Value=prod-snapshot-cleanup
```

### Manual Testing

Test Lambda function manually:
```bash
aws lambda invoke \
  --function-name prod-snapshot-cleanup \
  --log-type Tail \
  --query 'LogResult' \
  --output text \
  response.json | base64 -d

cat response.json
```

### Monitoring Best Practices

1. **CloudWatch Logs Insights**: Query logs for patterns
   ```sql
   fields @timestamp, @message
   | filter @message like /Deleting snapshot/
   | sort @timestamp desc
   | limit 100
   ```

2. **CloudWatch Dashboard**: Create dashboard with:
   - Lambda invocations
   - Error rate
   - Duration trends
   - Number of snapshots deleted (from logs)

3. **SNS Notifications**: Add SNS topic to CloudWatch alarms for email/Slack alerts

4. **X-Ray Tracing**: Enable for detailed performance analysis (optional)

## Project Structure

```
snapshot-cleanup/
├── README.md
├── config/
│   └── prod.json                  # Environment configuration
├── infra/
│   └── infra.yaml                 # Infrastructure CloudFormation template
├── app/
│   ├── app.yaml                   # Application CloudFormation template
│   └── lambda/
│       ├── lambda_function.py     # Lambda function code
│       └── requirements.txt       # Python dependencies
├── buildspec-infra.yml            # CodeBuild spec for infrastructure
└── buildspec-app.yml              # CodeBuild spec for application (uses jq to read config)
```

## Cleanup

To remove all resources:

```bash
# Delete application stack first
aws cloudformation delete-stack --stack-name snapshot-cleanup-app
aws cloudformation wait stack-delete-complete --stack-name snapshot-cleanup-app

# Delete infrastructure stack
aws cloudformation delete-stack --stack-name snapshot-cleanup-infra
aws cloudformation wait stack-delete-complete --stack-name snapshot-cleanup-infra

# Delete S3 artifacts (optional)
aws s3 rm s3://your-lambda-artifacts-bucket/snapshot-cleanup/ --recursive
```

## Troubleshooting

**Issue**: Lambda can't reach EC2 API
- **Solution**: Verify VPC endpoints are created and security group allows HTTPS outbound

**Issue**: Permission denied errors
- **Solution**: Check IAM role has `ec2:DescribeSnapshots` and `ec2:DeleteSnapshot` permissions

**Issue**: Snapshot deletion fails with "in use"
- **Solution**: Expected behavior for AMI-associated snapshots; check logs for error count

**Issue**: CloudFormation stack creation fails with "Export not found"
- **Solution**: Deploy infrastructure stack first before application stack

**Issue**: Lambda timeout
- **Solution**: Increase timeout in `app.yaml` (current: 300 seconds) or reduce snapshot count

## Security Considerations

1. **Least Privilege**: IAM role only has snapshot describe/delete permissions
2. **VPC Isolation**: Lambda runs in private subnet with no internet access
3. **VPC Endpoints**: Traffic to AWS APIs stays within AWS network
4. **Encryption**: Use encrypted snapshots and enable CloudWatch Logs encryption
5. **Audit Trail**: All actions logged to CloudWatch for compliance
6. **No Hardcoded Credentials**: Uses IAM roles for authentication

## Cost Estimation

**Monthly costs (approximate):**
- VPC Endpoints (2): ~$14.40 ($0.01/hour × 2 × 730 hours)
- Lambda: ~$0.20 (daily execution, ~2 seconds runtime)
- CloudWatch Logs: ~$0.50 (minimal log volume)
- S3 Storage: ~$0.02 (Lambda package)
- **Total**: ~$15/month

**Cost optimization:**
- VPC endpoints shared across multiple Lambdas reduce per-function cost
- Adjust log retention period to reduce storage costs
- Use S3 lifecycle policies for Lambda artifact cleanup
