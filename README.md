This project demonstrates how to build a highly optimized, lightweight AWS SageMaker Custom Inference Container for a Hugging Face Large Language Model (LLM).

We utilize `Qwen1.5-0.5B-Chat`, a highly capable but very small (0.5 billion parameter) instruction-tuned model. By using the CPU-only version of PyTorch, we keep the Docker image size extremely small, allowing it to run efficiently and cost-effectively on inexpensive SageMaker CPU instances (like `ml.t3.medium` or `ml.m5.large`).

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
docker build -t sagemaker-qwen-inference .
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
Run the following command in a new terminal window:
```bash
curl -X POST http://localhost:8080/invocations \
     -H "Content-Type: application/json" \
     -d '{"text": "Tell me three fun facts about space!"}'
```

### 4. Deploy to AWS SageMaker
To deploy this container to AWS, you will push the image to AWS Elastic Container Registry (ECR) and then configure SageMaker to create an endpoint from it.

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
Before creating the model in SageMaker, you must have an AWS IAM Role with the `AmazonSageMakerFullAccess` policy attached (or at minimum, a role with permissions to pull images from your ECR and write logs to CloudWatch). 

### 6. Create the Endpoint
1. Navigate to the **AWS SageMaker console**.
2. Go to **Models** -> **Create Model**.
3. Provide the ECR Image URI you just pushed.
4. Select or create your IAM Execution Role.
5. Create an **Endpoint Configuration** and deploy the model to an **Endpoint**!