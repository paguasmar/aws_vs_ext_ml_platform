# Deploying Truss on Baseten

Since Baseten created the open-source `truss` framework, deploying your model to their platform is by far the most native, automated, and streamlined experience available. 

Unlike RunPod or AWS SageMaker, you **do not** need to manually build Docker images, tag them, push them to ECR, or configure container registries. Baseten handles the entire infrastructure lifecycle automatically from a single CLI command!

## 1. Get a Baseten API Key
1. Go to your [Baseten account settings](https://app.baseten.co/settings/api_keys) and generate a new API key.

## 2. Authenticate the Truss CLI
In your terminal, authenticate your local environment with Baseten:
```bash
truss login
```
*(Paste your API key when prompted).*

## 3. Deploy the Model
Once authenticated, navigate to your project's root folder and simply run:

```bash
truss push .
```

### What happens in the background?
1. `truss` packages your model configuration, requirements, and logic.
2. It uploads the package directly to Baseten's secure infrastructure.
3. Baseten instantly spins up a heavy-duty builder node, natively constructs the Docker container, caches the layers, and provisions the exact CPU/GPU resources you defined in your `config.yaml` file.
4. It exposes a highly optimized, autoscaling serverless endpoint.

## 4. Test the Endpoint
After the `truss push` command finishes, your terminal will output a live Baseten URL (e.g., `https://model-<id>.api.baseten.co`).

You can test it using the Baseten Python SDK or via a standard curl request:

```bash
curl -X POST https://model-<id>.api.baseten.co/environments/production/predict \
  -H "Authorization: Api-Key <YOUR_BASETEN_API_KEY>" \
  -H "Content-Type: application/json" \
  -d @payload.json
```