# Deploying with Modal (The External AI Platform Way)

This project demonstrates how to deploy the exact same highly optimized `Qwen1.5-0.5B-Chat` Hugging Face LLM, but using **Modal** instead of AWS SageMaker. 

Modal is an external AI platform designed specifically for developers. It abstracts away the need to manage Dockerfiles, container registries, IAM roles, and API Gateways. The entire infrastructure—from the hardware requirements to the web endpoint—is defined entirely in Python.

## What We Need

Unlike the AWS approach which required a `Dockerfile`, `requirements.txt`, `app.py`, and complex bash scripts for API Gateways and Lambdas, Modal requires exactly **one** file:

1. **`modal_app.py`**: A single Python file that defines the container dependencies, loads the model into memory, and exposes a public web endpoint.

---

## How to Replicate and Use

### 1. Install and Authenticate
First, install the Modal client and link it to your account (you can sign up via GitHub).

```bash
pip install modal
modal setup
```

### 2. The Code (`modal_app.py`)
Create a file called `modal_app.py` and paste the following code. Notice how the Docker image and the web endpoint are defined as simple decorators.

```python
import modal
from pydantic import BaseModel

# 1. Define the App
app = modal.App("qwen-inference")

# 2. Define the Container Environment (Equivalent to Dockerfile + requirements.txt)
# We install PyTorch CPU version to keep it lightweight, just like the AWS version.
image = modal.Image.debian_slim(python_version="3.10").pip_install(
    "torch==2.0.1+cpu", 
    "transformers", 
    "accelerate",
    extra_index_url="https://download.pytorch.org/whl/cpu"
)

class InferenceRequest(BaseModel):
    text: str

# 3. Define the Web Endpoint and ML Class
@app.cls(image=image, min_containers=0)
class QwenModel:
    @modal.enter()
    def load_model(self):
        """This runs once when the container boots up to load the model into memory."""
        from transformers import AutoModelForCausalLM, AutoTokenizer
        import torch
        
        self.model_id = "Qwen/Qwen1.5-0.5B-Chat"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_id, 
            torch_dtype=torch.float32
        )

    @modal.web_endpoint(method="POST")
    def generate(self, item: InferenceRequest):
        """This is the actual web endpoint that handles the POST requests."""
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": item.text}
        ]
        
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        model_inputs = self.tokenizer([text], return_tensors="pt")
        generated_ids = self.model.generate(
            model_inputs.input_ids,
            max_new_tokens=512
        )
        
        generated_ids = [
            output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]
        
        response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
        return {"result": response}
```

### 3. Deploy to the Cloud
Deploying to the cloud is a single command. Modal automatically builds the container, pushes it to their registry, provisions the hardware, and gives you a public HTTPS endpoint.

```bash
modal deploy modal_app.py
```

*Output:*
```
✓ Created qwen-inference.
✓ Deployed web endpoint generate at: https://yourusername--qwen-inference-qwenmodel-generate.modal.run
```

### 4. Test the Deployed Endpoint
You now have a fully public, scalable web endpoint. Test it just like you did with AWS API Gateway!

```bash
# 1. Create a payload file
echo '{"text": "Tell me a fun fact about space."}' > payload.json

# 2. Invoke the endpoint (Replace with your actual Modal URL)
export MODAL_URL="https://yourusername--qwen-inference-qwenmodel-generate.modal.run"

curl -X POST $MODAL_URL \
     -H "Content-Type: application/json" \
     -d @payload.json \
     -o response.json

# 3. View the response
cat response.json
```

---

## Architectural Comparison: AWS vs Modal

| Feature | AWS SageMaker + API Gateway | Modal |
|---------|-----------------------------|-------|
| **Lines of Configuration/Bash** | ~150 lines | 0 lines |
| **Files Required** | `Dockerfile`, `requirements.txt`, `app.py`, `lambda_function.py`, `deployment.zip` | Just `modal_app.py` |
| **Cloud Steps** | ECR Push -> IAM Roles -> SageMaker Model -> SageMaker Endpoint Config -> SageMaker Endpoint -> Lambda IAM -> Lambda Proxy -> API Gateway -> API Gateway Deployment | `modal deploy` |
| **Cold Starts** | 15-30 seconds | 2-5 seconds |
| **Vendor Lock-in** | Low (Container runs anywhere) | High (Code uses Modal decorators) |

The trade-off is clear: AWS SageMaker gives you extreme control over the underlying infrastructure and zero lock-in, but requires immense DevOps knowledge. Modal abstracts everything away for a magical developer experience, but couples your code directly to their platform.
