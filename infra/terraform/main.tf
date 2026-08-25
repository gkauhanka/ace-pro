resource "aws_s3_bucket" "videos" {
  bucket = var.bucket_name
}

resource "aws_s3_bucket_ownership_controls" "videos" {
  bucket = aws_s3_bucket.videos.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_public_access_block" "videos" {
  bucket = aws_s3_bucket.videos.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "videos" {
  bucket = aws_s3_bucket.videos.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "videos" {
  bucket = aws_s3_bucket.videos.id

  rule {
    id     = "abort-incomplete-multipart-after-one-day"
    status = "Enabled"

    filter {}

    abort_incomplete_multipart_upload {
      days_after_initiation = 1
    }
  }
}

resource "aws_s3_bucket_cors_configuration" "videos" {
  count  = length(var.allowed_upload_origins) > 0 ? 1 : 0
  bucket = aws_s3_bucket.videos.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "HEAD", "PUT"]
    allowed_origins = var.allowed_upload_origins
    expose_headers  = ["ETag", "x-amz-checksum-sha256"]
    max_age_seconds = 3600
  }
}

resource "aws_cloudfront_origin_access_control" "videos" {
  name                              = "ace-pro-${var.environment}-videos"
  description                       = "Private S3 origin access for Ace Pro video playback"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "videos" {
  enabled         = true
  is_ipv6_enabled = true
  comment         = "Ace Pro ${var.environment} unlisted video playback"
  price_class     = var.cloudfront_price_class

  origin {
    domain_name              = aws_s3_bucket.videos.bucket_regional_domain_name
    origin_id                = "s3-${aws_s3_bucket.videos.id}"
    origin_access_control_id = aws_cloudfront_origin_access_control.videos.id
  }

  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "s3-${aws_s3_bucket.videos.id}"
    viewer_protocol_policy = "redirect-to-https"
    compress               = false
    cache_policy_id        = data.aws_cloudfront_cache_policy.caching_optimized.id
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
    minimum_protocol_version       = "TLSv1.2_2021"
  }
}

data "aws_cloudfront_cache_policy" "caching_optimized" {
  name = "Managed-CachingOptimized"
}

data "aws_iam_policy_document" "cloudfront_read" {
  statement {
    sid       = "AllowCloudFrontRead"
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.videos.arn}/*"]

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.videos.arn]
    }
  }
}

resource "aws_s3_bucket_policy" "cloudfront_read" {
  bucket = aws_s3_bucket.videos.id
  policy = data.aws_iam_policy_document.cloudfront_read.json

  depends_on = [aws_s3_bucket_public_access_block.videos]
}

data "aws_iam_policy_document" "video_api" {
  statement {
    sid = "ManageVideoObjects"
    actions = [
      "s3:AbortMultipartUpload",
      "s3:DeleteObject",
      "s3:GetObject",
      "s3:ListMultipartUploadParts",
      "s3:PutObject",
    ]
    resources = ["${aws_s3_bucket.videos.arn}/*"]
  }

  statement {
    sid = "InspectVideoBucketUploads"
    actions = [
      "s3:GetBucketLocation",
      "s3:ListBucketMultipartUploads",
    ]
    resources = [aws_s3_bucket.videos.arn]
  }

  statement {
    sid       = "InvalidateDeletedVideos"
    actions   = ["cloudfront:CreateInvalidation"]
    resources = [aws_cloudfront_distribution.videos.arn]
  }
}

resource "aws_iam_policy" "video_api" {
  name        = "ace-pro-${var.environment}-video-api"
  description = "Least-privilege storage operations for the Ace Pro video API"
  policy      = data.aws_iam_policy_document.video_api.json
}

