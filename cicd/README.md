# CI/CD IAM Roles

This CloudFormation template creates the necessary IAM roles for the CI/CD pipeline.

## Resources Created

1. **CodeBuild Service Role** - Allows CodeBuild to deploy infrastructure and application
2. **CodePipeline Service Role** - Allows CodePipeline to orchestrate the deployment
3. **S3 Bucket** - Stores pipeline artifacts with versioning and lifecycle policies

## Deployment

**Deploy this stack FIRST before setting up CodeBuild/CodePipeline projects.**

```bash
aws cloudformation create-stack \
  --stack-name snapshot-cleanup-cicd-roles \
  --template-body file://cicd/roles.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameters ParameterKey=ProjectName,ParameterValue=snapshot-cleanup
```

Wait for completion:
```bash
aws cloudformation wait stack-create-complete \
  --stack-name snapshot-cleanup-cicd-roles
```

## Get Role ARNs

After deployment, retrieve the role ARNs:

```bash
aws cloudformation describe-stacks \
  --stack-name snapshot-cleanup-cicd-roles \
  --query 'Stacks[0].Outputs'
```

## Use in CodeBuild Project

When creating CodeBuild project, use the CodeBuild role ARN from outputs:

```bash
aws codebuild create-project \
  --name snapshot-cleanup-infra-build \
  --source type=GITHUB,location=https://github.com/YOUR_USERNAME/snapshot-cleanup-lambda.git \
  --artifacts type=NO_ARTIFACTS \
  --environment type=LINUX_CONTAINER,image=aws/codebuild/standard:7.0,computeType=BUILD_GENERAL1_SMALL \
  --service-role arn:aws:iam::ACCOUNT_ID:role/snapshot-cleanup-codebuild-role
```

## Permissions Included

### CodeBuild Role
- CloudFormation: Full access to create/update/delete stacks
- EC2: Full access for VPC resources
- Lambda: Full access for Lambda functions
- IAM: Create and manage Lambda execution roles
- S3: Upload Lambda deployment packages
- EventBridge: Create scheduled rules
- CloudWatch Logs: Write build logs

### CodePipeline Role
- CodeBuild: Start builds and get build status
- S3: Store and retrieve pipeline artifacts
- CodeCommit/GitHub: Access source repositories
- CodeStar Connections: For GitHub integration

## Security Best Practices

- Roles follow least privilege principle with scoped permissions
- S3 bucket has encryption enabled
- Public access blocked on artifacts bucket
- Lifecycle policy deletes old artifacts after 30 days
- All resources tagged with project name
