# 🚀 Deployment Guide

Deploy the Pet Rescue System to production with confidence.

---

## Option 1: Streamlit Cloud (Recommended - Easiest)

### Prerequisites
- GitHub account
- Streamlit Cloud account (free)
- NVIDIA NIM API key

### Steps

1. **Push to GitHub**
```bash
git init
git add .
git commit -m "Initial commit: Pet Rescue System"
git remote add origin https://github.com/yourusername/pet-rescue-system.git
git push -u origin main
```

2. **Connect to Streamlit Cloud**
   - Visit: https://streamlit.io/cloud
   - Click "New app"
   - Select your GitHub repo
   - Set main file to `app.py`

3. **Add Secrets**
   - Click "Advanced Settings"
   - Under "Secrets", add:
   ```
   NVIDIA_NIM_API_KEY = "your_key_here"
   ```

4. **Deploy**
   - Click "Deploy"
   - Wait ~2 minutes
   - Share public URL

### Monitoring
- View logs in Streamlit Cloud dashboard
- Check app status in real-time
- Auto-redeploy on GitHub push

### Costs
- **Streamlit Cloud**: Free tier available
- **NVIDIA NIM APIs**: Free tier (10-30 requests/min)
- **Total**: $0/month ✅

---

## Option 2: Docker + Container Registry

### Prerequisites
- Docker installed
- Docker Hub account (or similar registry)
- Server with Docker (AWS, DigitalOcean, etc.)

### Create Dockerfile

**File: `Dockerfile`**
```dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

**File: `.dockerignore`**
```
__pycache__
*.pyc
.git
.gitignore
*.db
.env
.venv
.streamlit
```

### Build & Push

```bash
# Build image
docker build -t yourusername/pet-rescue:latest .

# Login to Docker Hub
docker login

# Push image
docker push yourusername/pet-rescue:latest
```

### Deploy to Server

```bash
# SSH into server
ssh user@your-server.com

# Pull image
docker pull yourusername/pet-rescue:latest

# Run container
docker run -d \
  -p 8501:8501 \
  -e NVIDIA_NIM_API_KEY="your_key" \
  -v /opt/pet-rescue/data:/app/data \
  --name pet-rescue \
  yourusername/pet-rescue:latest

# Check logs
docker logs -f pet-rescue
```

### Docker Compose

**File: `docker-compose.yml`**
```yaml
version: '3.8'

services:
  pet-rescue:
    image: yourusername/pet-rescue:latest
    ports:
      - "8501:8501"
    environment:
      - NVIDIA_NIM_API_KEY=${NVIDIA_NIM_API_KEY}
      - STREAMLIT_CLIENT_LOGGER_LEVEL=error
    volumes:
      - ./data:/app/data
      - ./metrics.db:/app/metrics.db
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Optional: Nginx reverse proxy
  nginx:
    image: nginx:latest
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      - pet-rescue
```

**Run**:
```bash
docker-compose up -d
```

---

## Option 3: Heroku (Deprecated - Use Streamlit Cloud Instead)

Heroku's free tier ended, but here's the process if using paid Heroku:

### Procfile
```
web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

### Deploy
```bash
heroku create your-app-name
heroku config:set NVIDIA_NIM_API_KEY=your_key
git push heroku main
heroku logs -t
```

---

## Option 4: AWS EC2

### Launch Instance
```bash
# Amazon Linux 2 or Ubuntu 20.04 LTS
# Instance type: t3.micro (free tier eligible)
# Security group: Allow 8501 (Streamlit)
```

### SSH & Install

```bash
# Connect
ssh -i key.pem ec2-user@your-instance.com

# Update system
sudo yum update -y  # Amazon Linux
# OR
sudo apt update && sudo apt upgrade -y  # Ubuntu

# Install Python
sudo yum install python3 python3-pip -y  # Amazon Linux
# OR
sudo apt install python3 python3-pip -y  # Ubuntu

# Clone repo
git clone https://github.com/yourusername/pet-rescue-system.git
cd pet-rescue-system

# Install dependencies
pip3 install -r requirements.txt

# Create .env
echo "NVIDIA_NIM_API_KEY=your_key" > .env

# Run with nohup (background)
nohup streamlit run app.py --server.port 8501 --server.address 0.0.0.0 &

# OR use systemd (better)
sudo tee /etc/systemd/system/pet-rescue.service > /dev/null <<EOF
[Unit]
Description=Pet Rescue Streamlit App
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/pet-rescue-system
ExecStart=/usr/local/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable pet-rescue
sudo systemctl start pet-rescue
sudo systemctl status pet-rescue
```

### Nginx Reverse Proxy

```bash
sudo yum install nginx -y
sudo systemctl start nginx
```

**Config: `/etc/nginx/sites-available/pet-rescue`**
```nginx
upstream streamlit {
    server localhost:8501;
}

server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    location / {
        proxy_pass http://streamlit;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

Enable:
```bash
sudo ln -s /etc/nginx/sites-available/pet-rescue /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### SSL Certificate (Let's Encrypt)

```bash
sudo yum install certbot python3-certbot-nginx -y
sudo certbot certonly --nginx -d your-domain.com
```

### Costs
- **EC2 t3.micro**: Free tier (1 year)
- **After free tier**: ~$8-15/month
- **Domain**: ~$12/year
- **Data transfer**: Minimal (~1-5 GB/month)
- **Total**: $0-20/month

---

## Option 5: DigitalOcean App Platform

### Deploy via GitHub

1. Connect GitHub account to DigitalOcean
2. Create new app
3. Select your repository
4. Choose "Streamlit" as service type
5. Add environment variable: `NVIDIA_NIM_API_KEY`
6. Deploy

### Costs
- **Basic**: $5-12/month
- **Includes**: 2GB RAM, auto-scaling

---

## Environment Variables

### Production .env

```bash
# NVIDIA NIM
NVIDIA_NIM_API_KEY=sk-xxx...

# Streamlit Config
STREAMLIT_CLIENT_LOGGER_LEVEL=error
STREAMLIT_LOGGER_LEVEL=error
STREAMLIT_CLIENT_SHOW_ERROR_DETAILS=false

# Database
DATABASE_URL=sqlite:///pet_rescue.db

# Optional: Monitoring
SENTRY_DSN=https://xxx...
LOG_LEVEL=INFO
```

### Secrets Management

**Option 1: Environment Variables**
```bash
export NVIDIA_NIM_API_KEY="your_key"
streamlit run app.py
```

**Option 2: Secrets File** (Streamlit)
```
~/.streamlit/secrets.toml
[general]
nvidia_nim_api_key = "your_key"
```

**Option 3: AWS Secrets Manager**
```python
import boto3
import json

def get_secret():
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId='pet-rescue-prod')
    secret = json.loads(response['SecretString'])
    return secret['NVIDIA_NIM_API_KEY']
```

**Option 4: HashiCorp Vault**
```python
import hvac

client = hvac.Client(url='https://vault.example.com')
secret = client.secrets.kv.read_secret_version(path='pet-rescue')
api_key = secret['data']['data']['NVIDIA_NIM_API_KEY']
```

---

## CI/CD Pipeline

### GitHub Actions Workflow

**File: `.github/workflows/deploy.yml`**
```yaml
name: Deploy to Streamlit Cloud

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest
    
    - name: Run tests
      run: python -m pytest tests/
    
    - name: Lint
      run: |
        pip install flake8
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
  
  deploy:
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Deploy to Streamlit Cloud
      run: |
        # Streamlit Cloud auto-deploys on GitHub push
        echo "Deployment triggered automatically"
```

---

## Monitoring & Logs

### View Logs

**Streamlit Cloud**:
- Dashboard → App → Logs tab

**Docker**:
```bash
docker logs -f pet-rescue
docker logs --tail 100 pet-rescue
```

**Systemd**:
```bash
journalctl -u pet-rescue -f
journalctl -u pet-rescue --since "10 minutes ago"
```

**Cloud Logging** (AWS CloudWatch):
```bash
aws logs tail /aws/ec2/pet-rescue --follow
```

### Performance Monitoring

```python
import time
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@monitor_performance
def process_case(image_base64):
    start = time.time()
    result = orchestrator.process_rescue_case(image_base64)
    duration = time.time() - start
    
    logger.info(f"Case processed in {duration:.2f}s")
    return result
```

---

## Backup & Recovery

### Database Backup

```bash
# Daily backup
0 2 * * * cp /app/metrics.db /backup/metrics.db.$(date +\%Y\%m\%d)

# Weekly upload to S3
0 3 * * 0 aws s3 cp /backup/metrics.db s3://bucket-name/backup/
```

### Restore from Backup

```bash
aws s3 cp s3://bucket-name/backup/metrics.db.20240101 ./metrics.db
```

---

## Scaling

### Horizontal Scaling

Use load balancer to distribute traffic:

```
Users
  ↓
Load Balancer
  ├─ Pet Rescue Instance 1 (8501)
  ├─ Pet Rescue Instance 2 (8502)
  └─ Pet Rescue Instance 3 (8503)
```

**AWS ALB Config**:
```
Target Group: pet-rescue
Port: 8501
Health Check: /_stcore/health
```

### Vertical Scaling

Increase instance resources:
- t3.micro → t3.small → t3.medium
- CPU: 1 → 2 → 4
- RAM: 1GB → 2GB → 4GB

### Caching

```python
@st.cache_resource
def get_orchestrator():
    return PetRescueOrchestrator()

@st.cache_data
def analyze_case(image_hash):
    return orchestrator.process_rescue_case(image_hash)
```

---

## Security Checklist

- [ ] API keys in environment variables
- [ ] HTTPS/SSL enabled
- [ ] IP whitelisting (if needed)
- [ ] Rate limiting enabled
- [ ] Input validation implemented
- [ ] Security headers set (CORS, CSP)
- [ ] Logs not showing sensitive data
- [ ] Regular backups scheduled
- [ ] Error pages don't expose details
- [ ] Dependencies updated regularly

---

## Troubleshooting

### App Won't Start
```bash
# Check Python version
python3 --version  # Must be 3.9+

# Check dependencies
pip install -r requirements.txt

# Test import
python3 -c "from agents import PetRescueOrchestrator"

# Check for syntax errors
python3 -m py_compile app.py
```

### API Connection Issues
```bash
# Test API key
curl -H "Authorization: Bearer $NVIDIA_NIM_API_KEY" \
  https://integrate.api.nvidia.com/v1/models

# Check network
ping integrate.api.nvidia.com

# Check firewall
sudo ufw status
```

### Performance Issues
```bash
# Check resource usage
top
df -h
free -h

# Restart app
sudo systemctl restart pet-rescue

# Increase memory limit (Docker)
docker update --memory 2g pet-rescue
```

---

## Support

- **Streamlit Docs**: https://docs.streamlit.io/
- **Streamlit Cloud Help**: https://discuss.streamlit.io/
- **NVIDIA NIM Docs**: https://docs.nvidia.com/nim/
- **Docker Docs**: https://docs.docker.com/

---

Last updated: 2024
