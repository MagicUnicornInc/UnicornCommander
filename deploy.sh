#!/bin/bash
# Build and deploy KDE AI Interface with container orchestration

# Build Docker image
docker build -t kde-ai-interface:latest .

# Deploy to Kubernetes
if command -v kubectl &> /dev/null; then
    kubectl apply -f kubernetes/deployment.yaml
elif command -v helm &> /dev/null; then
    helm install kde-ai-interface helm/
else
    echo "Neither kubectl nor helm found. Please install Kubernetes tools."
    exit 1
fi
