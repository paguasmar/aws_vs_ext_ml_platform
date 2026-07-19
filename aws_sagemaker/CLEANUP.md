# AWS Infrastructure Cleanup Guide

To completely tear down everything built in this guide and ensure you aren't charged for ongoing resources, you need to delete the resources in the reverse order that they were created. 

Run this bash script in your terminal to automatically hunt down and permanently delete the API Gateway, the Lambda proxy, the SageMaker endpoint, the ECR Docker images, and the IAM roles.

```bash
export AWS_REGION="us-east-1"
export ENDPOINT_NAME="qwen-inference-endpoint"
export ENDPOINT_CONFIG_NAME="qwen-inference-config"
export MODEL_NAME="qwen-inference-model"
export ECR_REPO_NAME="sagemaker-qwen-inference"
export LAMBDA_FUNCTION_NAME="sagemaker-invoker"
export LAMBDA_ROLE_NAME="sagemaker-lambda-role"
export SAGEMAKER_ROLE_NAME="sagemaker-role"

# 1. Find and Delete the API Gateway(s)
# If the creation script was run multiple times, there may be multiple gateways with the same name.
API_IDS=$(aws apigateway get-rest-apis --query "items[?name=='sagemaker-rest-api'].id" --output text --region $AWS_REGION)
for API_ID in $API_IDS; do
    if [ ! -z "$API_ID" ] && [ "$API_ID" != "None" ]; then
        echo "Deleting API Gateway $API_ID..."
        aws apigateway delete-rest-api --rest-api-id $API_ID --region $AWS_REGION
        sleep 2
    fi
done

# 2. Delete the Lambda Function
echo "Deleting Lambda Function..."
aws lambda delete-function --function-name $LAMBDA_FUNCTION_NAME --region $AWS_REGION

# 3. Delete Lambda IAM Role and its attached policies
echo "Deleting Lambda IAM Role..."
aws iam delete-role-policy --role-name $LAMBDA_ROLE_NAME --policy-name SageMakerInvokePolicy
aws iam detach-role-policy --role-name $LAMBDA_ROLE_NAME --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
aws iam delete-role --role-name $LAMBDA_ROLE_NAME

# 4. Delete SageMaker Endpoint, Config, and Model
echo "Deleting SageMaker Endpoint..."
aws sagemaker delete-endpoint --endpoint-name $ENDPOINT_NAME --region $AWS_REGION
aws sagemaker delete-endpoint-config --endpoint-config-name $ENDPOINT_CONFIG_NAME --region $AWS_REGION
aws sagemaker delete-model --model-name $MODEL_NAME --region $AWS_REGION

# 5. Delete ECR Repository and all Docker images inside it
echo "Deleting ECR Repository..."
aws ecr delete-repository --repository-name $ECR_REPO_NAME --force --region $AWS_REGION

# 6. Delete SageMaker IAM Role
echo "Deleting SageMaker IAM Role..."
aws iam detach-role-policy --role-name $SAGEMAKER_ROLE_NAME --policy-arn arn:aws:iam::aws:policy/AmazonSageMakerFullAccess
aws iam delete-role --role-name $SAGEMAKER_ROLE_NAME

echo "Cleanup Complete! You will no longer incur AWS charges for this project."
```
