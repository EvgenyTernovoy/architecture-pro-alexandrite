#!/bin/bash
set -euo pipefail

minikube delete

echo "=== 1. Запуск Minikube с ingress ==="
minikube start --addons=ingress

echo "=== 2. Установка cert-manager ==="
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.3/cert-manager.yaml

echo "Ожидание запуска pod-ов cert-manager..."
kubectl wait --namespace cert-manager \
  --for=condition=Available deployment \
  --timeout=180s \
  cert-manager cert-manager-cainjector cert-manager-webhook

echo "=== 3. Развертывание Jaeger Operator ==="
kubectl create namespace observability || true
kubectl apply -f https://github.com/jaegertracing/jaeger-operator/releases/download/v1.51.0/jaeger-operator.yaml -n observability

echo "Ожидание запуска pod-ов jaeger-operator..."
kubectl wait --namespace observability \
  --for=condition=Available deployment \
  --timeout=180s \
  jaeger-operator

echo "Применение конфигурации Jaeger instance..."
kubectl apply -f k8s/jaeger-instance.yaml

echo "=== 4. Сборка и деплой сервисов ==="
minikube image build -t service-a:latest services/service-a/
minikube image build -t service-b:latest services/service-b/

kubectl apply -f k8s/services.yaml

echo "Ожидание запуска сервисов..."
kubectl wait --for=condition=Ready pod -l app=service-a --timeout=180s
kubectl wait --for=condition=Ready pod -l app=service-b --timeout=180s

echo "=== ✅ Все компоненты развернуты ==="
echo "Для доступа к Jaeger UI выполни:"
echo "  kubectl port-forward svc/simplest-query 16686:16686"
echo "И открой http://localhost:16686"
