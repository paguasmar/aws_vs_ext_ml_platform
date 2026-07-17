# Cloud ML Architectures: Primitive AWS vs. External AI Platforms

This repository demonstrates the profound architectural differences between deploying a Large Language Model (LLM) on **raw AWS infrastructure (SageMaker)** versus deploying the exact same model on a modern **External AI Platform (Modal)**.

Both approaches deploy a highly optimized `Qwen1.5-0.5B-Chat` Hugging Face model using CPU-only PyTorch, providing a public, unsigned REST API endpoint. 

However, the developer experience and infrastructure overhead between the two is night and day.

---

## 📁 Repository Structure & Guides

Choose your deployment path to explore the technical guides for each approach:

### 1. [AWS SageMaker & API Gateway](./aws/README.md)
The **"Primitives"** approach. You manage the Dockerfiles, ECR repositories, IAM Roles, VPC networking, Lambda Proxies, and API Gateways.
- **Pros:** Extreme control, zero vendor lock-in, customizable at every layer.
- **Cons:** High DevOps burden, complex bash scripts, slower cold starts.

### 2. [External AI Platform (Modal)](./ext_ml_platform/README.md)
The **"Developer-First"** approach. The entire infrastructure—from container dependencies to web routing—is defined in a single Python script (`modal_app.py`).
- **Pros:** Zero devops, fast iterations, built-in scaling, and minimal code.
- **Cons:** High vendor lock-in, reliance on platform decorators.

---

## 📊 Architectural Comparison

| Feature | AWS (SageMaker + Lambda + API Gateway) | External Platform (Modal) |
|---------|----------------------------------------|---------------------------|
| **Lines of Configuration/Bash** | ~150 lines | 0 lines |
| **Files Required** | `Dockerfile`, `requirements.txt`, `app.py`, `lambda_function.py`, `deployment.zip` | Just `modal_app.py` |
| **Cloud Steps** | ECR Push -> IAM Roles -> SageMaker Model -> SageMaker Config -> SageMaker Endpoint -> Lambda IAM -> Lambda Proxy -> API Gateway -> Deployment | `modal deploy` |
| **Cold Starts** | 15-30 seconds | 2-5 seconds |
| **Autoscaling (Massive Scale)** | Infinite ceiling, absolute capacity control (slow cold boots) | Instant spike absorption, subject to platform quotas |
| **Pricing Model** | Complex (API GW + Lambda + SageMaker), cheaper at massive sustained scale | Simple (Per-second active compute), cheaper for spiky/idle workloads |
| **Vendor Lock-in** | Low (Container runs anywhere) | High (Code uses Modal decorators) |

---
*Explore the folders above to see the step-by-step implementations!*
