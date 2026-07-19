"""
The `Model` class is an interface between the ML model that you're packaging and the model
server that you're running it on.

The main methods to implement here are:
* `load`: runs exactly once when the model server is spun up or patched and loads the
   model onto the model server. Include any logic for initializing your model, such
   as downloading model weights and loading the model into memory.
* `predict`: runs every time the model server is called. Include any logic for model
  inference and return the model output.

See https://truss.baseten.co/quickstart for more.
"""


from transformers import pipeline

class Model:
    def __init__(self, **kwargs):
        self._model = None

    def load(self):
        # Load model here and assign to self._model.
        print("Loading Qwen model...")
        model_name = "Qwen/Qwen1.5-0.5B-Chat"
        self._model = pipeline("text-generation", model=model_name)
        print("Model loaded successfully.")

    def predict(self, model_input):
        # Run model inference here
        text = model_input.get("text", "")
        
        if not text:
            return {"error": "No 'text' provided in the request body."}
            
        # Format the prompt using the model's chat template
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": text}
        ]
        prompt = self._model.tokenizer.apply_chat_template(
            messages, 
            tokenize=False, 
            add_generation_prompt=True
        )
        
        # Run inference
        result = self._model(prompt, max_new_tokens=150, do_sample=True, top_p=0.95, temperature=0.7)

        # Extract only the generated response
        generated_text = result[0]["generated_text"]
        response_text = generated_text[len(prompt):].strip()
        
        return {"result": response_text}
