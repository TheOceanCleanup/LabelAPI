#!/bin/bash -e

# Select the namespace
echo "Enter namespace (staging/production):)"
read namespace

if ! [[ $namespace = "staging" || $namespace = "production" ]]; then
    echo "Aborting: Invalid namespace"
    exit
fi

# Checking if versions match
image=$(ls -1 | grep "image: tocacr.azurecr.io\/[a-zA-Z-]*:[0-9.]*" ./deploy/$namespace.yaml | head -1)
deploy_version=$(echo $image | sed 's/image: tocacr.azurecr.io\/[a-zA-Z-]*://')
git_version=$(git describe --tags --abbrev=0)

if ! [[ $git_version = $deploy_version ]]; then
    echo "Aborting: git version and $namespace version do not match"
    echo "Git version: $git_version, $namespace version: $deploy_version"
    echo "Please update $namespace version or run build.sh"
    exit
fi

echo "git version and $namespace version match"
echo "Version: $git_version"

# Connect to the correct Kubernetes cluster
az login
az account set --subscription "Microsoft Azure Sponsorship 2"
az aks get-credentials --resource-group toc-kubernetes --name toc-cluster

# Check if secrets are present
secrets=$(tr -d '[:blank:]\n' < ./deploy/$namespace.yaml | grep -o 'secretKeyRef:name:[a-zA-Z0-9-]*key' | sed 's/secretKeyRef:name://' | sed 's/key//' | uniq)
for s in $secrets; do
    kubectl get secret -n $namespace $s > /dev/null 2>&1 && echo "Secret $s exists"
done || (echo "Aborting: $s secret does not exist" && exit)

# Deploy to Kubernetes cluster
kubectl apply -f ./deploy/$namespace.yaml --record
kubectl get -f ./deploy/$namespace.yaml
