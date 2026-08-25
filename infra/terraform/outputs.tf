output "s3_bucket_name" {
  description = "S3 bucket used for original video objects."
  value       = aws_s3_bucket.videos.id
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID used for deletion invalidations."
  value       = aws_cloudfront_distribution.videos.id
}

output "playback_base_url" {
  description = "Base HTTPS URL for unlisted public video playback."
  value       = "https://${aws_cloudfront_distribution.videos.domain_name}"
}

output "video_api_policy_arn" {
  description = "IAM policy to attach to the future Python API runtime role."
  value       = aws_iam_policy.video_api.arn
}

