# Cloud Deployment

This guide covers deploying UAMS in cloud environments.

![Cloud Deployment](../images/cloud-deployment.png)

## Cloud Overview

UAMS can be deployed on various cloud platforms:

- **AWS**: Amazon Web Services
- **Azure**: Microsoft Azure
- **GCP**: Google Cloud Platform
- **Other**: Any cloud provider supporting Docker/Kubernetes

## Cloud Deployment Options

### Platform as a Service (PaaS)

Deploy on managed platforms:

- **Heroku**: Easy deployment
- **AWS Elastic Beanstalk**: AWS managed platform
- **Azure App Service**: Azure managed platform
- **Google App Engine**: GCP managed platform

### Container as a Service (CaaS)

Deploy using containers:

- **AWS ECS**: Amazon Elastic Container Service
- **Azure Container Instances**: Azure containers
- **Google Cloud Run**: GCP serverless containers
- **Docker Swarm**: Container orchestration

### Kubernetes

Deploy on Kubernetes:

- **AWS EKS**: Amazon Elastic Kubernetes Service
- **Azure AKS**: Azure Kubernetes Service
- **GKE**: Google Kubernetes Engine
- **Self-managed**: Your own Kubernetes cluster

## AWS Deployment

### Architecture

```
Internet
    ↓
AWS Application Load Balancer
    ↓
ECS Fargate / EC2 Instances
    ↓
RDS PostgreSQL
    ↓
ElastiCache Redis
    ↓
S3 (Static/Media Files)
```

### Configuration

#### ECS Task Definition

```json
{
  "family": "uams",
  "networkMode": "awsvpc",
  "containerDefinitions": [
    {
      "name": "uams",
      "image": "your-account.dkr.ecr.region.amazonaws.com/uams:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://user:pass@rds-endpoint:5432/uams_db"
        }
      ],
      "secrets": [
        {
          "name": "SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:uams/secret-key"
        }
      ]
    }
  ]
}
```

#### RDS Configuration

```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('RDS_DB_NAME'),
        'USER': os.environ.get('RDS_USERNAME'),
        'PASSWORD': os.environ.get('RDS_PASSWORD'),
        'HOST': os.environ.get('RDS_HOSTNAME'),
        'PORT': os.environ.get('RDS_PORT', '5432'),
    }
}
```

#### S3 for Static/Media Files

```python
# settings.py
# Use django-storages
INSTALLED_APPS += ['storages']

AWS_STORAGE_BUCKET_NAME = 'uams-static-media'
AWS_S3_REGION_NAME = 'us-east-1'
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'

STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
```

### Deployment Steps

1. **Build Docker Image**:
   ```bash
   docker build -t uams:latest .
   ```

2. **Push to ECR**:
   ```bash
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin account.dkr.ecr.us-east-1.amazonaws.com
   docker tag uams:latest account.dkr.ecr.us-east-1.amazonaws.com/uams:latest
   docker push account.dkr.ecr.us-east-1.amazonaws.com/uams:latest
   ```

3. **Create ECS Service**:
   ```bash
   aws ecs create-service \
     --cluster uams-cluster \
     --service-name uams-service \
     --task-definition uams \
     --desired-count 3
   ```

## Azure Deployment

### Architecture

```
Internet
    ↓
Azure Load Balancer
    ↓
Azure Container Instances / App Service
    ↓
Azure Database for PostgreSQL
    ↓
Azure Cache for Redis
    ↓
Azure Blob Storage
```

### Configuration

#### App Service Configuration

```bash
# Azure CLI
az webapp create \
  --resource-group uams-rg \
  --plan uams-plan \
  --name uams-app \
  --deployment-container-image-name your-registry.azurecr.io/uams:latest
```

#### Database Configuration

```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('AZURE_DB_NAME'),
        'USER': os.environ.get('AZURE_DB_USER'),
        'PASSWORD': os.environ.get('AZURE_DB_PASSWORD'),
        'HOST': os.environ.get('AZURE_DB_HOST'),
        'PORT': '5432',
        'OPTIONS': {
            'sslmode': 'require',
        }
    }
}
```

## GCP Deployment

### Architecture

```
Internet
    ↓
GCP Load Balancer
    ↓
Cloud Run / GKE
    ↓
Cloud SQL (PostgreSQL)
    ↓
Memorystore (Redis)
    ↓
Cloud Storage
```

### Configuration

#### Cloud Run

```yaml
# cloud-run.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: uams
spec:
  template:
    spec:
      containers:
      - image: gcr.io/project-id/uams:latest
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: uams-secrets
              key: database-url
```

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Run migrations
RUN python manage.py migrate

# Expose port
EXPOSE 8000

# Run application
CMD ["gunicorn", "user_access_management.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/uams_db
    depends_on:
      - db
      - redis

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=uams_db
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

## Kubernetes Deployment

### Deployment Manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: uams
spec:
  replicas: 3
  selector:
    matchLabels:
      app: uams
  template:
    metadata:
      labels:
        app: uams
    spec:
      containers:
      - name: uams
        image: uams:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: uams-secrets
              key: database-url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: uams-secrets
              key: secret-key
---
apiVersion: v1
kind: Service
metadata:
  name: uams-service
spec:
  selector:
    app: uams
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

## Cloud Best Practices

### Security

1. **Secrets Management**: Use cloud secrets managers
2. **Encryption**: Encrypt data at rest and in transit
3. **Network Security**: Use VPCs and security groups
4. **Access Control**: Implement IAM policies
5. **Monitoring**: Enable security monitoring

### Performance

1. **Auto-scaling**: Configure auto-scaling
2. **Caching**: Use managed cache services
3. **CDN**: Use CDN for static files
4. **Database**: Use managed database services
5. **Monitoring**: Monitor performance metrics

### Cost Optimization

1. **Right-sizing**: Choose appropriate instance sizes
2. **Reserved Instances**: Use reserved instances for predictable workloads
3. **Spot Instances**: Use spot instances for non-critical workloads
4. **Storage**: Optimize storage usage
5. **Monitoring**: Monitor and optimize costs

## Environment Configuration

### Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Cache
REDIS_URL=redis://host:6379/0

# Storage
AWS_STORAGE_BUCKET_NAME=uams-bucket
AWS_S3_REGION_NAME=us-east-1

# Application
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com
```

## Monitoring and Logging

### CloudWatch (AWS)

```python
# Log to CloudWatch
import logging
import watchtower

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(watchtower.CloudWatchLogHandler())
```

### Application Insights (Azure)

```python
# Azure Application Insights
from opencensus.ext.azure.log_exporter import AzureLogHandler

logger = logging.getLogger(__name__)
logger.addHandler(AzureLogHandler())
```

## Next Steps

- [Installation & Upgrade](installation_upgrade.md) - Installation guide
- [Configuration](configuration.md) - Configuration options
- [Enterprise](enterprise.md) - Enterprise features

---

For cloud-specific deployment assistance, consult your cloud provider's documentation or support team.

