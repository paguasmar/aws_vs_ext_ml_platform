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
| **Vendor Lock-in** | Low (Container runs anywhere) | High (Code uses Modal decorators) |

---

## 📈 Autoscaling Dynamics (At Massive Scale)

If money is no object and you need to scale to thousands of concurrent clients, the choice between these two architectures comes down to **Speed of Scaling** vs. **Absolute Capacity Control**.

### AWS SageMaker: The "Infinite Ceiling"
If you switch from Serverless SageMaker (which has hard concurrency limits) to **Provisioned SageMaker Endpoints**, AWS scales to infinity.
* **The Benefit:** You have absolute, granular control over Auto Scaling Groups (ASGs). You can purchase Capacity Reservations to guarantee entire racks of servers are dedicated exclusively to your model. For sustained, massive traffic (like Netflix), AWS is the ultimate winner.
* **The Drawback:** EC2 instances take time to boot. If traffic spikes from 100 to 10,000 users in 30 seconds, ASGs will trigger, but clients may experience timeouts during the 3-5 minute boot delay.

### External Platform (Modal): The "Spike Absorber"
Modal pools massive amounts of global compute and relies on a highly optimized, lightweight container runtime (gVisor).
* **The Benefit:** If traffic spikes to 1,000 requests in 5 seconds, Modal will aggressively fan out to 1,000 parallel containers almost instantly. For unpredictable, highly "spiky" traffic, Modal dramatically outperforms standard AWS Auto Scaling because its cold-start penalty is virtually zero.
* **The Drawback:** You share a multi-tenant platform with internal quotas. You cannot reserve dedicated hardware in advance, meaning you are at the mercy of their available capacity pool during massive global spikes.

---
*Explore the folders above to see the step-by-step implementations!*
