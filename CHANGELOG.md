# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-01-15

### Added
- Initial release of EC2 Snapshot Cleanup Lambda
- Automated snapshot deletion based on configurable retention period (default 365 days)
- VPC-isolated Lambda function deployed in private subnet
- CloudFormation Infrastructure as Code templates:
  - `infra.yaml` - VPC, subnets, security groups, VPC endpoints, IAM roles
  - `app.yaml` - Lambda function, EventBridge rules, CloudWatch Logs
- EventBridge scheduled trigger (daily at 2 AM UTC via cron expression)
- VPC endpoints for EC2 and CloudWatch Logs (no NAT Gateway required)
- CI/CD pipeline setup with AWS CodeBuild:
  - `buildspec-infra.yml` - Infrastructure deployment
  - `buildspec-app.yml` - Application deployment with automated packaging
- Configuration management via `config/prod.json` for environment-specific settings
- IAM roles and S3 bucket for CI/CD artifacts (`cicd/roles.yaml`)
- CloudWatch Logs integration with 30-day retention policy
- Comprehensive documentation:
  - Deployment instructions
  - Architecture diagrams
  - Monitoring and troubleshooting guides
  - Cost estimation

### Security
- VPC isolation with no direct internet access
- Private subnet deployment for Lambda function
- VPC endpoints for secure AWS API communication
- Security groups with HTTPS-only egress (port 443)
- IAM roles following least privilege principle
- Encrypted S3 bucket (AES256) for Lambda artifacts
- Public access blocked on all S3 buckets
- Versioning enabled on artifact bucket
- Lifecycle policies for automatic artifact cleanup (90 days)

### Infrastructure
- VPC with configurable CIDR (default: 10.0.0.0/16)
- Private subnet (default: 10.0.1.0/24)
- Interface VPC endpoints for EC2 and CloudWatch Logs
- Lambda function: Python 3.11, 256MB memory, 5-minute timeout
- CloudWatch Log Group with 30-day retention
- EventBridge rule for scheduled execution

### Configuration
- Retention period: 365 days (configurable)
- Schedule: Daily at 2 AM UTC (configurable)
- VPC CIDR blocks (configurable)
- S3 bucket name (configurable)
- Environment name (default: prod)

[1.0.0]: https://github.com/YOUR_USERNAME/snapshot-cleanup-lambda/releases/tag/v1.0.0
