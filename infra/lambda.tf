# Lambda execution role
resource "aws_iam_role" "lambda_role" {
  name = "hello-world-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Attach basic execution policy
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.lambda_role.name
}

# Lambda function code
data "archive_file" "lambda_zip" {
  type        = "zip"
  output_path = "${path.module}/lambda_function.zip"

  source {
    content  = <<EOF
from datetime import datetime

def lambda_handler(event, context):
    return {
        'message': {'data': 'hello world'},
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }
EOF
    filename = "lambda_function.py"
  }
}

# Lambda function
resource "aws_lambda_function" "hello_world" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "hello-world-resolver"
  role            = aws_iam_role.lambda_role.arn
  handler         = "lambda_function.lambda_handler"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  runtime         = "python3.11"
  timeout         = 30
}

# AppSync data source for Lambda
resource "aws_appsync_datasource" "lambda_datasource" {
  api_id           = aws_appsync_graphql_api.graphql.id
  name             = "hello_world_lambda"
  service_role_arn = aws_iam_role.appsync_lambda_role.arn
  type             = "AWS_LAMBDA"

  lambda_config {
    function_arn = aws_lambda_function.hello_world.arn
  }
}

# IAM role for AppSync to invoke Lambda
resource "aws_iam_role" "appsync_lambda_role" {
  name = "appsync-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "appsync.amazonaws.com"
        }
      }
    ]
  })
}

# Policy to allow AppSync to invoke Lambda
resource "aws_iam_role_policy" "appsync_lambda_policy" {
  name = "appsync-lambda-policy"
  role = aws_iam_role.appsync_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = aws_lambda_function.hello_world.arn
      }
    ]
  })
}

# AppSync resolver
resource "aws_appsync_resolver" "hello_world_resolver" {
  api_id      = aws_appsync_graphql_api.graphql.id
  type        = "Query"
  field       = "helloWorld"
  data_source = aws_appsync_datasource.lambda_datasource.name

  runtime {
    name            = "APPSYNC_JS"
    runtime_version = "1.0.0"
  }

  code = <<EOF
import { util } from '@aws-appsync/utils';

export function request(ctx) {
  return {
    operation: 'Invoke',
    payload: ctx.arguments,
  };
}

export function response(ctx) {
  return ctx.result;
}
EOF
}

# Lambda authorizer function
data "archive_file" "authorizer_zip" {
  type        = "zip"
  output_path = "${path.module}/authorizer_function.zip"

  source {
    content  = <<EOF
def lambda_handler(event, context):
    return {
        'isAuthorized': True,
        'ttlOverride': 300
    }
EOF
    filename = "authorizer_function.py"
  }
}

resource "aws_lambda_function" "authorizer" {
  filename         = data.archive_file.authorizer_zip.output_path
  function_name    = "appsync-lambda-authorizer"
  role            = aws_iam_role.lambda_role.arn
  handler         = "authorizer_function.lambda_handler"
  source_code_hash = data.archive_file.authorizer_zip.output_base64sha256
  runtime         = "python3.11"
  timeout         = 30
}

# Lambda permission for AppSync to invoke authorizer
resource "aws_lambda_permission" "appsync_authorizer" {
  statement_id  = "AllowAppSyncInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.authorizer.function_name
  principal     = "appsync.amazonaws.com"
  source_arn    = aws_appsync_graphql_api.graphql.arn
}

output "lambda_function_name" {
  value       = aws_lambda_function.hello_world.function_name
  description = "Lambda function name"
}

output "authorizer_function_name" {
  value       = aws_lambda_function.authorizer.function_name
  description = "Lambda authorizer function name"
}
