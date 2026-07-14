import os
from fastapi import FastAPI, Request, Response
from pydantic import BaseModel
from transformers import pipeline

class InvocationRequest(BaseModel):
    text: str

app = FastAPI(title="SageMaker HuggingFace Inference API")

print("Loading model...")

# Runs in cheap CPU instances (like ml.t3.medium or ml.m5.large) without running out of memory.
model_name = "Qwen/Qwen1.5-0.5B-Chat"
generator = pipeline("text-generation", model=model_name)
print("Model loaded successfully.")

@app.get("/ping")
async def ping():
    """
    SageMaker health check endpoint.
    Must return 200 OK if the container is ready to accept requests.
    """
    return Response(status_code=200)

@app.post("/invocations")
async def invocations(request_data: InvocationRequest):
    """
    SageMaker inference endpoint.
    Receives the payload, performs prediction, and returns the result.
    """
    try:
        text = request_data.text
        
        if not text:
            return {"error": "No 'text' provided in the request body."}, 400
            
        # Format the prompt using the model's chat template
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": text}
        ]
        prompt = generator.tokenizer.apply_chat_template(
            messages, 
            tokenize=False, 
            add_generation_prompt=True
        )
        
        # Run inference
        # Limit max_new_tokens to keep generation fast on CPUs
        result = generator(prompt, max_new_tokens=150, do_sample=True, top_p=0.95, temperature=0.7)
        
        # Extract only the generated response
        generated_text = result[0]["generated_text"]
        response_text = generated_text[len(prompt):].strip()
        
        return {"result": response_text}
    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == "__main__":
    import uvicorn
    # SageMaker typically uses port 8080 for inference containers
    port = int(os.environ.get("AIP_HTTP_PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
