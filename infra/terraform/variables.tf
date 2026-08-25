variable "aws_region" {
  description = "AWS region for the S3 bucket and application backend."
  type        = string
  default     = "us-west-2"
}

variable "environment" {
  description = "Deployment environment name used for tagging and resource names."
  type        = string
  default     = "development"
}

variable "bucket_name" {
  description = "Globally unique S3 bucket name for original videos."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$", var.bucket_name))
    error_message = "bucket_name must be a valid lowercase S3 bucket name."
  }
}

variable "allowed_upload_origins" {
  description = "Browser origins allowed to send presigned multipart uploads to S3."
  type        = list(string)
  default     = []
}

variable "cloudfront_price_class" {
  description = "CloudFront geographic price class for public playback."
  type        = string
  default     = "PriceClass_100"

  validation {
    condition = contains(
      ["PriceClass_100", "PriceClass_200", "PriceClass_All"],
      var.cloudfront_price_class,
    )
    error_message = "cloudfront_price_class must be PriceClass_100, PriceClass_200, or PriceClass_All."
  }
}

