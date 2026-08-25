# Ace Pro AWS video storage

This Terraform configuration defines the production-shaped storage resources without an RDS database:

- private Amazon S3 bucket for original videos;
- default S3 server-side encryption;
- public-access blocking and bucket-owner-enforced ownership;
- CORS for direct browser/iOS multipart uploads;
- cleanup of incomplete multipart uploads after one day;
- CloudFront distribution with origin access control for unlisted playback; and
- an IAM policy for the future Python API runtime role.

## Not included

- RDS PostgreSQL;
- a Python API compute/runtime service;
- DNS or a custom CloudFront certificate;
- an AWS account or remote Terraform state backend.

## Validate locally

```bash
terraform init -backend=false
terraform fmt -check -recursive
terraform validate
```

## Future deployment

Copy `terraform.tfvars.example` to an ignored `terraform.tfvars`, choose a globally unique bucket name, configure an AWS account/profile, review `terraform plan`, and request explicit approval before applying it.

