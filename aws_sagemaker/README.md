This project demonstrates how to build a highly optimized, lightweight AWS SageMaker Custom Inference Container for a Hugging Face Large Language Model (LLM).

We utilize `Qwen1.5-0.5B-Chat`, a highly capable but very small (0.5 billion parameter) instruction-tuned model. By using the CPU-only version of PyTorch, we keep the Docker image size extremely small, allowing it to run efficiently and cost-effectively on inexpensive SageMaker CPU instances (like `ml.t2.medium` or `ml.m5.large`).

## What We Built
1. **FastAPI Application (`app.py`)**: A lightweight web server that meets AWS SageMaker's endpoint requirements:
   - `GET /ping`: For SageMaker health checks.
   - `POST /invocations`: The inference endpoint that accepts text and returns the model's generated response.
2. **Optimized Dependencies (`requirements.txt`)**: Pinned dependencies configured to pull PyTorch CPU wheels, saving over 4.5GB of Docker image bloat.
3. **SageMaker Dockerfile (`Dockerfile`)**: A minimal Python 3.10 setup that exposes port `8080` (expected by SageMaker) and runs our FastAPI app without unnecessary C/C++ compiler toolchains.

## How to Replicate and Use

### 1. Build the Docker Image
To package the model and application into a Docker container, run the following command from the root of the project. Because we've stripped out the heavy GPU libraries, the build will be quick and the image size will be highly optimized:

```bash
docker build --provenance=false -t sagemaker-qwen-inference .
```

### 2. Run the Container
Before deploying to AWS, you can run the container locally to ensure it is working correctly:

```bash
docker run -p 8080:8080 sagemaker-qwen-inference
```

*Note: The first time the container starts, it will download the Hugging Face model weights (around 1GB) into memory. This may take a minute or two.*

### 3. Send an Inference Request
Once the container is running, you can test it by sending a payload to the `/invocations` endpoint. SageMaker natively uses port `8080`.

**Option A: Using the built-in UI**
Open your browser and navigate to the automatically generated documentation UI to test requests easily:
[http://localhost:8080/docs](http://localhost:8080/docs)

**Option B: Using the Terminal (cURL)**
Run the following commands in a new terminal window:
```bash
echo '{"text": "Tell me three fun facts about space!"}' > payload.json

curl -X POST http://localhost:8080/invocations \
     -H "Content-Type: application/json" \
     -d @payload.json \
     -o response.json

cat response.json
```

### 4. Deploy to AWS SageMaker
To deploy this container to AWS, you will push the image to AWS Elastic Container Registry (ECR) and then configure SageMaker to create an endpoint from it.

**Prerequisites**
1. **Docker Login**: Make sure you are logged into Docker by running:
   ```bash
   docker login
   ```
2. **AWS Authentication**: Before running the deployment script, you must authenticate your AWS CLI:
   - In the AWS IAM Console, go to your user's **Security credentials** tab and create an **Access Key**.
   - Run the following command in your terminal and paste your Access Key ID and Secret Access Key when prompted:
     ```bash
     aws configure
     ```

Once you have completed the prerequisites, run the following script to build and push your image:

```bash
# 1. Define your AWS variables (update the region if necessary)
export AWS_REGION="us-east-1" 
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export ECR_REPO_NAME="sagemaker-qwen-inference"

# 2. Authenticate Docker with AWS ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# 3. Create the repository
aws ecr create-repository --repository-name $ECR_REPO_NAME --region $AWS_REGION

# 4. Tag the image
docker tag sagemaker-qwen-inference:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME:latest

# 5. Push to ECR
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME:latest
```

### 5. Create a SageMaker Execution Role
Before creating the model in SageMaker, you must create an AWS IAM Role that allows SageMaker to access resources on your behalf (such as pulling images from ECR and writing logs to CloudWatch).
1. In the AWS IAM Console, create a new Role.
2. Select **AWS service** as the Trusted entity type.
3. Choose **SageMaker** as the service, and **SageMaker - Execution** as the use case.
4. Attach the `AmazonSageMakerFullAccess` permissions policy.
5. Name the role `sagemaker-role` and create it.

### 6. Create the Endpoint
You can create the SageMaker endpoint either through the AWS Console or automatically via the AWS CLI.

**Option A: Using the AWS Console**
1. Navigate to the **AWS SageMaker console**.
2. Go to **Models** -> **Create Model**.
3. Provide the ECR Image URI you just pushed.
4. Select your `sagemaker-role` IAM Execution Role.
5. Create an **Endpoint Configuration** (using a CPU instance like `ml.m5.large`) and deploy the model to an **Endpoint**.

**Option B: Using the AWS CLI**
Run the following script to automate the creation of the model, endpoint configuration, and endpoint deployment:

```bash
export MODEL_NAME="qwen-inference-model"
export ENDPOINT_CONFIG_NAME="qwen-inference-config"
export ENDPOINT_NAME="qwen-inference-endpoint"
export ROLE_ARN="arn:aws:iam::$AWS_ACCOUNT_ID:role/sagemaker-role"
export IMAGE_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME:latest"

# 1. Create the Model
aws sagemaker create-model \
    --model-name $MODEL_NAME \
    --primary-container Image=$IMAGE_URI \
    --execution-role-arn $ROLE_ARN \
    --region $AWS_REGION

# 2. Create a Serverless Endpoint Configuration
aws sagemaker create-endpoint-config \
    --endpoint-config-name $ENDPOINT_CONFIG_NAME \
    --production-variants "VariantName=AllTraffic,ModelName=$MODEL_NAME,ServerlessConfig={MemorySizeInMB=3072,MaxConcurrency=1}" \
    --region $AWS_REGION

# 3. Create the Endpoint
aws sagemaker create-endpoint \
    --endpoint-name $ENDPOINT_NAME \
    --endpoint-config-name $ENDPOINT_CONFIG_NAME \
    --region $AWS_REGION

echo "Creating endpoint... This can take 5-10 minutes."
aws sagemaker wait endpoint-in-service --endpoint-name $ENDPOINT_NAME --region $AWS_REGION
echo "Endpoint is ready! Name: $ENDPOINT_NAME"
```

### 7. Test the Deployed Endpoint
Now that your endpoint is running in the cloud, you can test it securely using the AWS CLI. 

Run the following command in your terminal. This will send a prompt to your model and save the output to `response.json`:

```bash
# 1. Create a payload file
echo '{"text": "Tell me a fun fact about space."}' > payload.json

# 2. Invoke the endpoint
aws sagemaker-runtime invoke-endpoint \
    --endpoint-name qwen-inference-endpoint \
    --region us-east-1 \
    --content-type application/json \
    --body fileb://payload.json \
    response.json

# View the response:
cat response.json
```

### 8. Expose the Endpoint via API Gateway (Optional)
If you want to call your model via a public, unsigned HTTP endpoint (like `curl`), you can wrap the SageMaker endpoint in an AWS Lambda function and expose it through an Amazon API Gateway.

Run the following script to automatically create the Lambda proxy, increase its timeout to 29 seconds (to allow for longer LLM generations), and create a public REST API URL:

```bash
export ENDPOINT_NAME="qwen-inference-endpoint"
export LAMBDA_ROLE_NAME="sagemaker-lambda-role"
export LAMBDA_FUNCTION_NAME="sagemaker-invoker"
export AWS_REGION="us-east-1"
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# 1. Create the Lambda Python code
cat << 'EOF' > lambda_function.py
import json
import boto3
import os

sagemaker_runtime = boto3.client('sagemaker-runtime', region_name=os.environ.get('AWS_REGION', 'us-east-1'))

def lambda_handler(event, context):
    # Fetch the SageMaker endpoint name from environment variables
    endpoint_name = os.environ.get('ENDPOINT_NAME', 'qwen-inference-endpoint')
    
    try:
        # If 'body' exists as a string, it's an HTTP request (API Gateway)
        if 'body' in event and isinstance(event['body'], str):
            payload = event['body']
        # Otherwise, it's a direct CLI invocation
        else:
            payload = json.dumps(event)
        
        # Forward directly to SageMaker
        response = sagemaker_runtime.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType='application/json',
            Body=payload
        )
        
        result = json.loads(response['Body'].read().decode('utf-8'))
        
        return {
            'statusCode': 200, 
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(result)
        }
        
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
EOF

# 2. Package the code
zip deployment.zip lambda_function.py

# 3. Create the Lambda IAM Role (Trust Policy)
aws iam create-role \
    --role-name $LAMBDA_ROLE_NAME \
    --assume-role-policy-document '{"Version": "2012-10-17","Statement": [{"Action": "sts:AssumeRole","Principal": {"Service": "lambda.amazonaws.com"},"Effect": "Allow"}]}'

# 4. Attach basic execution policy (allows Lambda to write logs to CloudWatch)
aws iam attach-role-policy \
    --role-name $LAMBDA_ROLE_NAME \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# 5. Add inline policy to allow the Lambda to invoke your SageMaker endpoint
aws iam put-role-policy \
    --role-name $LAMBDA_ROLE_NAME \
    --policy-name SageMakerInvokePolicy \
    --policy-document '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": "sagemaker:InvokeEndpoint",
                "Resource": "arn:aws:sagemaker:'$AWS_REGION':'$AWS_ACCOUNT_ID':endpoint/'$ENDPOINT_NAME'"
            }
        ]
    }'

# Wait 15 seconds for IAM role to propagate
echo "Waiting 15 seconds for IAM role to propagate..."
sleep 15

# 6. Create the Lambda Function and set a 29-second timeout
aws lambda create-function \
    --function-name $LAMBDA_FUNCTION_NAME \
    --runtime python3.10 \
    --role arn:aws:iam::$AWS_ACCOUNT_ID:role/$LAMBDA_ROLE_NAME \
    --handler lambda_function.lambda_handler \
    --zip-file fileb://deployment.zip \
    --timeout 29 \
    --environment "Variables={ENDPOINT_NAME=$ENDPOINT_NAME}" \
    --region $AWS_REGION

# 7. Create a public REST API pointing to the Lambda
API_ID=$(aws apigateway create-rest-api --name 'sagemaker-rest-api' --region $AWS_REGION --query 'id' --output text)
PARENT_ID=$(aws apigateway get-resources --rest-api-id $API_ID --region $AWS_REGION --query 'items[0].id' --output text)

aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $PARENT_ID \
    --http-method POST \
    --authorization-type "NONE" \
    --region $AWS_REGION

aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $PARENT_ID \
    --http-method POST \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri arn:aws:apigateway:$AWS_REGION:lambda:path/2015-03-31/functions/arn:aws:lambda:$AWS_REGION:$AWS_ACCOUNT_ID:function:$LAMBDA_FUNCTION_NAME/invocations \
    --region $AWS_REGION

# 8. Grant API Gateway permission to invoke the Lambda
aws lambda add-permission \
    --function-name $LAMBDA_FUNCTION_NAME \
    --statement-id apigateway-rest-api-$(date +%s) \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:$AWS_REGION:$AWS_ACCOUNT_ID:$API_ID/*/POST/" \
    --region $AWS_REGION

# 9. Deploy the API to a "prod" URL
aws apigateway create-deployment \
    --rest-api-id $API_ID \
    --stage-name prod \
    --region $AWS_REGION

# 10. Output the new URL and Test it
API_URL="https://$API_ID.execute-api.$AWS_REGION.amazonaws.com/prod/"
echo -e "\n\nSuccess! Your completely public, unsigned API URL is: $API_URL\n"

sleep 5

echo '{"text": "What is the capital of France?"}' > payload.json

curl -X POST $API_URL \
     -H "Content-Type: application/json" \
     -d @payload.json \
     -o response.json

cat response.json
```

---

### 🗑️ Infrastructure Cleanup
When you are done experimenting, it is highly recommended to delete your AWS resources so you do not incur ongoing charges. 
Please refer to the **[AWS Cleanup Guide](./CLEANUP.md)** for a script that safely tears down the entire infrastructure in the exact reverse order of creation.