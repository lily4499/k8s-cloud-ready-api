## Kubernetes Cloud-Ready API” (Python FastAPI + Terraform + EKS/AKS)

> I built and deployed a production-style Python FastAPI API on AWS EKS using Terraform for all the infrastructure (VPC, subnets, EKS cluster, node group). I containerized the app with Docker, scanned images with Trivy before pushing them to ECR, and deployed to Kubernetes using Deployment, Service, and ALB-backed Ingress.
> For observability, I installed the kube-prometheus-stack (Prometheus, Grafana, Alertmanager) and configured Slack alerts for key conditions like high pod restarts or CPU usage. I also created a Jenkins pipeline to automate build → scan → push → deploy.

This repository contains all the files referenced below; refer to each file in the GitHub tree for implementation details.

```

---

# Kubernetes Cloud-Ready API on AWS EKS

Python **FastAPI** backend deployed on **Amazon EKS** using:

- **Terraform** – VPC, subnets, EKS cluster, node group  
- **Docker + Trivy** – containerization & image scanning  
- **Kubernetes** – Deployment, Service, Ingress (ALB)  
- **Prometheus + Grafana + Alertmanager** – monitoring & alerts  
- (Optional) **Jenkins** – CI/CD pipeline

This project is designed as a **production-style DevOps portfolio project** and can be used in interviews to demonstrate skills in cloud, Kubernetes, IaC, observability, and DevSecOps.

---

## 1. High-Level Architecture

Flow (simplified):

`Client → AWS ALB (Ingress) → Kubernetes Service → FastAPI Pods on EKS → CloudWatch/Prometheus/Grafana/Alertmanager`

Main components:

- **FastAPI app**: simple API with `/health` and `/items`
- **Docker image**: built locally, scanned by **Trivy**, pushed to **ECR**
- **Terraform**: provisions VPC, public/private subnets, EKS cluster, node group
- **Kubernetes**: runs the app and exposes it externally via Ingress + ALB
- **Monitoring**: kube-prometheus-stack (Prometheus, Grafana, Alertmanager) with Slack alerts

---

## 2. Prerequisites

- AWS account with IAM user/role configured (`aws configure`)
- AWS CLI installed  
- kubectl installed  
- Terraform installed  
- Docker installed and running  
- Helm v3 installed  
- (Optional) Jenkins server/agent with Docker + AWS CLI + kubectl + Trivy  
- A Slack workspace + **Incoming Webhook URL** (for alerts)

---

## 3. Environment Variables

Set these in your shell (adjust values to your account):

```bash
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=<your_aws_account_id>
export ECR_REPO_NAME=cloud-ready-api
export CLUSTER_NAME=cloud-ready-api-cluster
````

Derived values:

```bash
export ECR_URI=${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}
```

---

## 4. Project Structure

*(File names only – see GitHub repo for contents.)*

```text
.
├── app/
│   ├── main.py                  # FastAPI application
│   ├── requirements.txt         # Python dependencies
│   └── Dockerfile               # Docker image definition
│
├── infra/
│   ├── providers.tf             # Terraform provider configuration (AWS)
│   ├── variables.tf             # Input variables (region, project_name, etc.)
│   ├── vpc.tf                   # VPC, subnets, IGW, route tables
│   ├── eks.tf                   # EKS cluster + node group + IAM roles
│   └── outputs.tf               # Terraform outputs (cluster name, endpoint, CA)
│
├── k8s/
│   ├── namespace.yaml           # Namespace for app (cloud-api)
│   ├── deployment.yaml          # FastAPI Deployment
│   ├── service.yaml             # NodePort Service
│   └── ingress.yaml             # Ingress (AWS ALB)
│
├── k8s/monitoring/
│   ├── monitoring-namespace.yaml    # Namespace: monitoring
│   ├── prometheus-values.yaml       # Helm values override for kube-prometheus-stack
│   └── alertmanager-config.yaml     # Alertmanager config + Slack webhook (as Secret)
│
├── scans/
│   └── (optional Trivy reports)     # e.g., trivy-report.json
│
├── Jenkinsfile                   # Optional Jenkins CI/CD pipeline
└── README.md                     # This file
```

---

## 5. Step-by-Step Guide

### 5.1 Clone the Repository

```bash
git clone <YOUR_REPO_URL> k8s-cloud-ready-api
cd k8s-cloud-ready-api
```

---

### 5.2 Local Development – Run FastAPI

From `app/`:

```bash
cd app
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

uvicorn main:app --host 0.0.0.0 --port 8000
```

Test in browser:

* `http://localhost:8000/health`
* `http://localhost:8000/items`

---

### 5.3 Build and Run Docker Image Locally

From `app/`:

```bash
cd app

# Build image
docker build -t cloud-ready-api:1 .

# Run container
docker run -d --name cloud-ready-api -p 8000:8000 cloud-ready-api:1

# Test
curl http://localhost:8000/health
curl http://localhost:8000/items

# Cleanup
docker stop cloud-ready-api
docker rm cloud-ready-api
```

---

### 5.4 Install Trivy and Scan the Image

Install Trivy (Debian/Ubuntu):

```bash
sudo apt update
sudo apt install wget apt-transport-https gnupg -y
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
echo deb https://aquasecurity.github.io/trivy-repo/deb generic main | sudo tee /etc/apt/sources.list.d/trivy.list
sudo apt update
sudo apt install trivy -y
```

Scan the local image:

```bash
trivy image cloud-ready-api:1
```

(Optionally save a report:)

```bash
mkdir -p scans
trivy image --format json --output scans/trivy-report.json cloud-ready-api:1
```

---

### 5.5 Create ECR Repository and Push Image

Create ECR repo:

```bash
aws ecr create-repository \
  --repository-name ${ECR_REPO_NAME} \
  --region ${AWS_REGION}
```

Login Docker to ECR:

```bash
aws ecr get-login-password --region ${AWS_REGION} \
  | docker login \
    --username AWS \
    --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
```

Tag and push:

```bash
cd app

IMAGE_TAG=1
docker tag cloud-ready-api:${IMAGE_TAG} ${ECR_URI}:${IMAGE_TAG}
docker push ${ECR_URI}:${IMAGE_TAG}
```

---

### 5.6 Provision AWS Infrastructure with Terraform

From `infra/`:

```bash
cd infra

terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

After apply, note the outputs:

* `cluster_name`
* `cluster_endpoint`
* `cluster_ca`

---

### 5.7 Configure kubectl for EKS

```bash
aws eks update-kubeconfig \
  --name ${CLUSTER_NAME} \
  --region ${AWS_REGION}

# Verify connection
kubectl get nodes
kubectl get ns
```

---

### 5.8 Deploy FastAPI App to EKS (Kubernetes Manifests)

From `k8s/`:

#### 1. Update image in `deployment.yaml`

Set the container image to the ECR image you pushed:

```text
image: "<AWS_ACCOUNT_ID>.dkr.ecr.<AWS_REGION>.amazonaws.com/cloud-ready-api:1"
```

#### 2. Apply manifests

```bash
cd k8s

kubectl apply -f namespace.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml

kubectl get pods -n cloud-api
kubectl get svc -n cloud-api
kubectl get ingress -n cloud-api
```

When Ingress is ready, you’ll see an **ADDRESS** (ALB DNS).

Test:

```bash
curl http://<ALB_DNS>/health
curl http://<ALB_DNS>/items
```

---

## 6. Monitoring Stack (Prometheus, Grafana, Alertmanager)

### 6.1 Create Monitoring Namespace

From `k8s/monitoring/`:

```bash
kubectl apply -f monitoring-namespace.yaml
kubectl get ns
```

### 6.2 Create Alertmanager Slack Config Secret

Edit `k8s/monitoring/alertmanager-config.yaml` with your:

* Slack **webhook URL**
* Slack **channel name**

Apply:

```bash
kubectl apply -f alertmanager-config.yaml
kubectl get secret -n monitoring
```

### 6.3 Install kube-prometheus-stack via Helm

Add repo:

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
```

Install the stack:

```bash
helm install monitoring prometheus-community/kube-prometheus-stack \
  -n monitoring \
  -f prometheus-values.yaml
```

Check pods/services:

```bash
kubectl get pods -n monitoring
kubectl get svc -n monitoring
```

Find Grafana external endpoint (LoadBalancer service):

```bash
kubectl get svc -n monitoring
```

Login:

* URL: Grafana LoadBalancer EXTERNAL-IP
* User: `admin`
* Password: value set in `prometheus-values.yaml`

---

## 7. Test Slack Alerts

### 7.1 Test Slack Webhook directly (from terminal)

```bash
curl -X POST \
  -H 'Content-type: application/json' \
  --data '{"text":"✅ Test alert from Cloud-Ready API project"}' \
  https://hooks.slack.com/services/YOUR/WEBHOOK/PATH
```

You should see the message in your Slack channel.

### 7.2 Create a Test Alert in Prometheus

From `k8s/monitoring/`:

Add and apply a rule file (example name in repo):

```bash
kubectl apply -f test-alert-rule.yaml
kubectl get prometheusrules -n monitoring
```

When the alert fires, Alertmanager should send a message to Slack via the configuration in `alertmanager-config.yaml`.

To clean up:

```bash
kubectl delete -f test-alert-rule.yaml
```

---

## 8. Optional: Jenkins CI/CD Pipeline

The `Jenkinsfile` in the repo defines a Declarative Pipeline that:

1. Checks out code
2. Builds the Docker image
3. Scans image with Trivy
4. Logs in to ECR
5. Pushes image to ECR
6. Updates image in `k8s/deployment.yaml`
7. Applies Kubernetes manifests to EKS

### 8.1 Required Jenkins Tools/Setup

* Jenkins agent with:

  * Docker
  * AWS CLI
  * kubectl
  * Trivy
* Jenkins credentials:

  * AWS credentials or configured IAM role
* Environment variables in Jenkinsfile:

  * `AWS_DEFAULT_REGION`
  * `ECR_REPO`
  * `CLUSTER_NAME`

Run pipeline from Jenkins with this repo as SCM and watch stages:

* **Checkout**
* **Build & Test**
* **Docker Build**
* **Security Scan - Trivy**
* **Push to ECR**
* **Deploy to EKS**

---

## 9. Cleanup

To avoid AWS charges:

```bash
cd infra
terraform destroy
```

Also delete ECR images/repo if no longer needed:

```bash
aws ecr delete-repository \
  --repository-name ${ECR_REPO_NAME} \
  --force \
  --region ${AWS_REGION}
```

---
# Steps to create ALB Controller

# 1. Associate OIDC Provider
eksctl utils associate-iam-oidc-provider \
  --cluster $CLUSTER_NAME \
  --region $AWS_REGION \
  --approve

# 2. Download AWS Load Balancer Controller IAM Policy
curl -o iam-policy.json \
  https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/main/docs/install/iam_policy.json

# 3. Create IAM Policy
aws iam create-policy \
  --policy-name AWSLoadBalancerControllerIAMPolicy \
  --policy-document file://iam-policy.json

# 4. Create IAM Service Account for ALB Controller
eksctl create iamserviceaccount \
  --cluster $CLUSTER_NAME \
  --region $AWS_REGION \
  --namespace kube-system \
  --name aws-load-balancer-controller \
  --attach-policy-arn arn:aws:iam::$AWS_ACCOUNT_ID:policy/AWSLoadBalancerControllerIAMPolicy \
  --approve

# 5. Add Helm Repo
helm repo add eks https://aws.github.io/eks-charts
helm repo update

# 6. Install AWS Load Balancer Controller
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=$CLUSTER_NAME \
  --set serviceAccount.create=false \
  --set region=$AWS_REGION \
  --set vpcId=$VPC_ID \
  --set serviceAccount.name=aws-load-balancer-controller

---

# ✅ **Check if AWS Load Balancer Controller is Installed**

```bash
kubectl get deployment -n kube-system aws-load-balancer-controller
```

---

# ✅ **Check Pod Status**

```bash
kubectl get pods -n kube-system | grep aws-load-balancer-controller
```

---

# ✅ **Check Logs (verify it's running with no errors)**

```bash
kubectl logs -n kube-system deployment/aws-load-balancer-controller
```

---

---
## Some challenges i overcome

> **Challenge:**
> When I was exposing a Kubernetes service through AWS ALB Ingress, the Ingress resource was created but no Application Load Balancer ever showed up in the AWS console. The Ingress stayed in a “pending” state with no clear error.
>
> **What was wrong:**
> I had defined the annotations for the AWS Load Balancer Controller, but I forgot the most important field:
>
> ```yaml
> spec:
>   ingressClassName: alb
> ```
>
> Without the correct `ingressClassName`, the controller completely ignored my Ingress, so nothing got provisioned.
>
> **How I solved it:**
> I checked `kubectl describe ingress` and the controller logs, realized the Ingress was not being picked up, added:
>
> ```yaml
> spec:
>   ingressClassName: alb
> ```
>
> re-applied the manifest, and then the ALB was created successfully and started routing traffic.
>
> **Lesson learned:**
> Now, whenever I work with AWS Load Balancer Controller, I always double-check `ingressClassName: alb` first, because a missing or wrong ingress class can waste a lot of troubleshooting time.

---

---

**Challenge:**
I deployed my Kubernetes Service for the API, and the application was working correctly from a user perspective, but in my monitoring stack (Prometheus/Grafana) I was not seeing any application metrics. The app was healthy, but the dashboards stayed empty, which made it harder to monitor and alert on it.

**Root cause:**
The issue was in the Service metadata. The Service was missing this label:

```yaml
metadata:
  labels:
    app: cloud-ready-api
```

My Prometheus/ServiceMonitor configuration was selecting Services by `app=cloud-ready-api`. Because that label was missing on the Service, Prometheus never discovered it, so metrics were never scraped—even though the app itself was running fine.

**How I debugged it:**

* First I verified the app worked:

  * `kubectl get svc -n cloud-api`
  * Hit the Service/Ingress URL in the browser or via `curl`.
* Then I checked why Prometheus didn’t see it:

  * `kubectl get svc cloud-ready-api-svc -n cloud-api --show-labels`
  * I noticed the `app=cloud-ready-api` label was missing on the Service.
* I compared that with the ServiceMonitor/Prometheus config, which was filtering on `app=cloud-ready-api`.

**Fix:**
I updated the Service to include the label:

```yaml
metadata:
  name: cloud-ready-api-svc
  namespace: cloud-api
  labels:
    app: cloud-ready-api
```

Re-applied the manifest, and then Prometheus started scraping the metrics, and the Grafana dashboard populated correctly.

**Lesson learned:**
Now, whenever I set up monitoring in Kubernetes, I always double-check that **Service labels match the label selectors used by Prometheus/ServiceMonitor**. The app can be running and reachable, but without the right label on the Service, you get “no data” in monitoring and waste time troubleshooting the wrong thing.

---
---

**Challenge:**
I deployed the kube-prometheus-stack with my own `prometheus-values.yaml`, where I tried to define Alertmanager + Slack settings directly in that file. Prometheus and Grafana came up, but **Alertmanager never got created and no alerts were sent to Slack**, even when my test alert rule should have fired.

**Root cause:**
I had mixed up **Helm chart values** and the **actual Alertmanager configuration**.
I put the Slack config inside `prometheus-values.yaml`, but the chart was configured to:

```yaml
alertmanager:
  alertmanagerSpec:
    useExistingSecret: true
    configSecret: alertmanager-monitoring-config
```

That means Alertmanager expects its config (including Slack route/receiver) to come from an **external Secret**, not from values directly. Since that secret/config wasn’t properly defined, Alertmanager was never created/initialized as expected.

**How I debugged it:**

* Checked the monitoring namespace:

  * `kubectl get pods -n monitoring` → no Alertmanager pod.
* Inspected the Helm release:

  * `helm get values monitoring -n monitoring`
* Reviewed the chart docs and realized that with `useExistingSecret: true`, the Slack config must live in a **separate Alertmanager config file/secret**, not just in `prometheus-values.yaml`.

**Fix:**

1. I **removed the Slack config** block from `prometheus-values.yaml` and kept only the reference to the secret.

2. I created a dedicated `alertmanager-config.yaml` with the proper Alertmanager config + Slack receiver:

3. Applied the config/secret and reinstalled/upgraded the Helm release.

4. After that, **Alertmanager pod came up**, and my test alert started firing to the Slack `#alerts` channel.

**Lesson learned:**
Now I’m very careful with **how Helm charts expect configuration to be injected**—especially for components like Alertmanager.



