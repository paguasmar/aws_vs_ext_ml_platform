import modal
from pydantic import BaseModel

# 1. Define the App
app = modal.App("qwen-inference")

# 2. Define the Container Environment (Equivalent to Dockerfile + requirements.txt)
image = modal.Image.debian_slim(python_version="3.10").pip_install(
    "torch==2.0.1+cpu", 
    "transformers", 
    "accelerate",
    extra_index_url="https://download.pytorch.org/whl/cpu"
)

class InferenceRequest(BaseModel):
    text: str

# 3. Define the Web Endpoint and ML Class
@app.cls(image=image, keep_warm=0)
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
