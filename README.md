# AWS vs External ML Platforms

This repository demonstrates the exact same ML workload (serving a highly-optimized HuggingFace LLM, `Qwen1.5-0.5B-Chat`) deployed across four entirely different architectural paradigms.

The goal is to compare the traditional, heavy-duty "Cloud Primitive" approach (AWS) with modern, developer-first AI infrastructure platforms.

---

## 📁 The Four Architectures

Choose your deployment path to explore the technical guides and code for each approach:

### 1. [Pure AWS: SageMaker & API Gateway](./aws_sagemaker/)
The **"Primitives"** approach. You manually manage the Dockerfiles, ECR registries, IAM Roles, VPC networking, Lambda Proxies, and API Gateways.
- **Pros:** Extreme control, zero vendor lock-in, customizable at every networking layer, meets strict enterprise compliance.
- **Cons:** Massive DevOps burden, complex bash deployment scripts, slower cold starts, steep learning curve.

### 2. [Truss + RunPod + AWS ECR](./truss_runpod_ecr/)
The **"Open-Source Hybrid"** approach. You use the open-source `truss` framework to package the model, push the container to a secure private AWS registry, and run it on dedicated RunPod GPU instances.
- **Pros:** Low lock-in (Truss is open source), access to incredibly cheap dedicated GPUs (RunPod), secure enterprise storage (ECR).
- **Cons:** Still requires manual infrastructure plumbing between the registry and the compute provider.

### 3. [Truss + Baseten](./truss_baseten/)
The **"Managed ML Serverless"** approach. You use the exact same open-source `truss` logic from Option 2, but push it directly to Baseten (the creators of Truss) using a single CLI command.
- **Pros:** Zero-ops infrastructure. Baseten handles the Docker build, the registry, and the GPU provisioning automatically. Very fast cold starts optimized specifically for LLMs.
- **Cons:** You pay a serverless premium for compute compared to dedicated RunPod instances.

### 4. [Modal (Pure Python Serverless)](./modal_serverless/)
The **"Developer-First"** approach. The entire infrastructure—from container OS dependencies to web routing and GPU allocation—is defined entirely inside a single Python script via decorators.
- **Pros:** The ultimate developer experience. Zero Dockerfiles, zero YAML. Instant deployments and incredibly fast cold-starts.
- **Cons:** High vendor lock-in (your code is heavily coupled to the Modal Python SDK).

---

## 📊 Architectural Comparison

| Feature | 1. Pure AWS | 2. Truss + RunPod | 3. Truss + Baseten | 4. Modal |
|---------|-------------|-------------------|--------------------|----------|
| **Setup Complexity** | Very High | Medium | Very Low | Very Low |
| **Code Required** | `Dockerfile`, `app.py`, `lambda.py`, `deployment.zip`, `bash` | `config.yaml`, `model.py` | `config.yaml`, `model.py` | Just `modal_app.py` |
| **Deployment Flow** | ECR Push -> IAM -> SageMaker Model -> Endpoint -> API Gateway | ECR Push -> RunPod UI Setup | `truss push` | `modal deploy` |
| **Vendor Lock-in** | Low (Raw Container) | Low (Truss is Open Source) | Low (Truss is Open Source) | High (Platform SDK) |
| **Cold Starts** | 15-30+ seconds | 10-20s (RunPod Serverless) | 2-5 seconds | 2-5 seconds |
| **Best For...** | Strict Enterprise Compliance / Full AWS environments | Cost-efficient 24/7 dedicated GPU workloads | Zero-ops scalable LLM APIs | Fast iterations & spiky data pipelines |
