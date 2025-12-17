terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  backend "s3" {
    bucket = "cjo-terraform"
    key    = "open-rag-search/terraform.tfstate"
    region = "us-east-1"
  }
}

# Configure the AWS Provider
provider "aws" {
  region = "us-east-1"
}

resource "aws_appsync_graphql_api" "graphql" {
  authentication_type = "AWS_LAMBDA"
  name                = "appsync-graphql"

  lambda_authorizer_config {
    authorizer_uri = aws_lambda_function.authorizer.arn
  }

  schema = <<EOF
type Query {
  helloWorld: HelloWorldResponse
}

type HelloWorldResponse {
  message: MessageData!
  timestamp: AWSDateTime!
}

type MessageData {
  data: String!
}
EOF
}

resource "aws_appsync_api_key" "graphql_api_key" {
  api_id  = aws_appsync_graphql_api.graphql.id
  expires = timeadd(timestamp(), "8760h") # 1 year from now
}

resource "aws_ssm_parameter" "graphql_api_key" {
  name        = "/appsync/graphql_api_key/api-key"
  description = "API Key for Graphql Chat Events API"
  type        = "SecureString"
  value       = aws_appsync_api_key.graphql_api_key.key
}

resource "aws_appsync_api" "chat_events" {
  name = "example-event-api"

  event_config {
    auth_provider {
      auth_type = "API_KEY"
    }

    connection_auth_mode {
      auth_type = "API_KEY"
    }

    default_publish_auth_mode {
      auth_type = "API_KEY"
    }

    default_subscribe_auth_mode {
      auth_type = "API_KEY"
    }
  }
}

resource "aws_appsync_channel_namespace" "default_namespace" {
  api_id = aws_appsync_api.chat_events.api_id
  name   = "default"
}

resource "aws_appsync_api_key" "chat_events_api_key" {
  api_id  = aws_appsync_api.chat_events.api_id
  expires = timeadd(timestamp(), "8760h") # 1 year from now
}

resource "aws_ssm_parameter" "appsync_api_key" {
  name        = "/appsync/chat-events/api-key"
  description = "API Key for AppSync Chat Events API"
  type        = "SecureString"
  value       = aws_appsync_api_key.chat_events_api_key.key
}

resource "aws_cloudfront_cache_policy" "appsync_cache_policy" {
  name        = "appsync-cache-policy"
  comment     = "Cache policy for AppSync API"
  default_ttl = 0
  max_ttl     = 0
  min_ttl     = 0

  parameters_in_cache_key_and_forwarded_to_origin {
    cookies_config {
      cookie_behavior = "none"
    }

    headers_config {
      header_behavior = "none"
    }

    query_strings_config {
      query_string_behavior = "none"
    }

    enable_accept_encoding_gzip   = false
    enable_accept_encoding_brotli = false
  }
}

resource "aws_cloudfront_origin_request_policy" "appsync_origin_request_policy" {
  name    = "appsync-origin-request-policy"
  comment = "Origin request policy for AppSync API with WebSocket support"

  cookies_config {
    cookie_behavior = "none"
  }

  headers_config {
    header_behavior = "whitelist"
    headers {
      items = [
        "x-api-key",
        "Content-Type",
        "Accept",
        "Sec-WebSocket-Key",
        "Sec-WebSocket-Version",
        "Sec-WebSocket-Protocol",
        "Sec-WebSocket-Extensions"
      ]
    }
  }

  query_strings_config {
    query_string_behavior = "all"
  }
}

resource "aws_cloudfront_distribution" "appsync_distribution" {
  enabled = true
  comment = "CloudFront distribution for AppSync API"

  origin {
    domain_name = replace(aws_appsync_api.chat_events.dns["HTTP"], "https://", "")
    origin_id   = "appsync-http-origin"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  origin {
    domain_name = trimsuffix(trimprefix(aws_appsync_graphql_api.graphql.uris["GRAPHQL"], "https://"), "/graphql")
    origin_id   = "appsync-graphql-origin"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  origin {
    domain_name = replace(aws_appsync_api.chat_events.dns["REALTIME"], "wss://", "")
    origin_id   = "appsync-websocket-origin"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  default_cache_behavior {
    allowed_methods            = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods             = ["GET", "HEAD", "OPTIONS"]
    target_origin_id           = "appsync-http-origin"
    viewer_protocol_policy     = "https-only"
    cache_policy_id            = aws_cloudfront_cache_policy.appsync_cache_policy.id
    origin_request_policy_id   = aws_cloudfront_origin_request_policy.appsync_origin_request_policy.id
  }

  ordered_cache_behavior {
    path_pattern               = "/event*"
    allowed_methods            = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods             = ["GET", "HEAD", "OPTIONS"]
    target_origin_id           = "appsync-websocket-origin"
    viewer_protocol_policy     = "https-only"
    cache_policy_id            = aws_cloudfront_cache_policy.appsync_cache_policy.id
    origin_request_policy_id   = aws_cloudfront_origin_request_policy.appsync_origin_request_policy.id
  }

  ordered_cache_behavior {
    path_pattern               = "/endpoint/*"
    allowed_methods            = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods             = ["GET", "HEAD", "OPTIONS"]
    target_origin_id           = "appsync-graphql-origin"
    viewer_protocol_policy     = "https-only"
    cache_policy_id            = aws_cloudfront_cache_policy.appsync_cache_policy.id
    origin_request_policy_id   = aws_cloudfront_origin_request_policy.appsync_origin_request_policy.id
  }

   ordered_cache_behavior {
    path_pattern               = "/graphql"
    allowed_methods            = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods             = ["GET", "HEAD", "OPTIONS"]
    target_origin_id           = "appsync-graphql-origin"
    viewer_protocol_policy     = "https-only"
    cache_policy_id            = aws_cloudfront_cache_policy.appsync_cache_policy.id
    origin_request_policy_id   = aws_cloudfront_origin_request_policy.appsync_origin_request_policy.id
  }


  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }
}

output "cloudfront_domain_name" {
  value       = aws_cloudfront_distribution.appsync_distribution.domain_name
  description = "CloudFront distribution domain name"
}

output "appsync_http_url" {
  value       = aws_appsync_api.chat_events.dns["HTTP"]
  description = "AppSync HTTP URL"
}

output "appsync_websocket_url" {
  value       = aws_appsync_api.chat_events.dns["REALTIME"]
  description = "AppSync WebSocket URL"
}

output "appsync_api_key_parameter" {
  value       = aws_ssm_parameter.appsync_api_key.name
  description = "SSM Parameter name containing the AppSync API key"
}

output "graphql_api_key_parameter" {
  value       = aws_ssm_parameter.graphql_api_key.name
  description = "SSM Parameter name containing the Graphql API key"
}

output "graphql_api_url" {
  value       = aws_appsync_graphql_api.graphql.uris["GRAPHQL"]
  description = "GraphQL API endpoint URL"
}

output "graphql_api_id" {
  value       = aws_appsync_graphql_api.graphql.id
  description = "GraphQL API ID"
}


