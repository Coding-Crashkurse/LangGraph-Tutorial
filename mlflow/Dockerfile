FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir mlflow

EXPOSE 5000

CMD ["mlflow", "server", "--backend-store-uri", "sqlite:///mlflow.db", "--host", "0.0.0.0", "--port", "5000"]
