# Deployment Guide

This guide covers deploying the TCO Web Platform to production.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Variables](#environment-variables)
- [Building for Production](#building-for-production)
- [Deployment Options](#deployment-options)
- [Post-Deployment](#post-deployment)
- [Monitoring and Maintenance](#monitoring-and-maintenance)

## Prerequisites

Before deploying to production, ensure you have:

- PostgreSQL 15+ database (managed service recommended)
- Redis 7+ instance (managed service recommended)
- Python 3.11+ runtime environment
- Node.js 20+ for building the frontend
- SSL certificate for HTTPS
- Domain name configured

## Environment Variables

### Backend Environment Variables

Create a `.env` file or set environment variables in your hosting platform:

```bash
# Application
ENVIRONMENT=production
PROJECT_NAME="TCO Web Platform API"
VERSION=0.1.0
API_V1_PREFIX=/api/v1

# Database
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname

# Redis Cache
REDIS_URL=redis://host:6379/0
SESSION_TTL_SECONDS=1800

# CORS (comma-separated list of allowed origins)
BACKEND_CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Caching
CACHE_RESULTS=true
```

### Important Database URL Notes

- The `DATABASE_URL` should use the `postgresql+asyncpg://` scheme for async support
- For managed PostgreSQL services (like Neon, Supabase, or RDS), use the connection string provided
- SSL is automatically handled for cloud database services
- Do not include `sslmode` parameters in the URL (handled automatically)

### Frontend Environment Variables

Create a `.env.production` file in the `frontend/` directory:

```bash
# API endpoint
VITE_API_BASE_URL=https://yourdomain.com/api/v1
```

## Building for Production

### 1. Generate Shared Data Layer

Ensure the TypeScript frontend has the latest data from Python sources:

```bash
python scripts/generate_vehicle_catalog_ts.py
python scripts/export_tco_snapshot.py
```

### 2. Build Frontend

```bash
cd frontend
npm install
npm run build
```

This creates optimized static files in `frontend/dist/`.

### 3. Prepare Backend

```bash
pip install -r requirements.txt
```

## Deployment Options

### Option 1: Replit Deployments (Recommended)

The easiest deployment path is using Replit's built-in autoscale deployment:

1. **Verify deployment configuration** - The project is configured with:
   - **Run command**: `uvicorn backend.app.main:app --host 0.0.0.0 --port 8000`
   - **Build command**: `cd frontend && npm install && npm run build`
   - **Port mapping**: Internal port 8000 → External port 80

2. **Configure environment variables** in the Secrets panel (see below)

3. **Click "Deploy"** in your Replit workspace

4. Replit will automatically:
   - Build the frontend static files
   - Start the backend on port 8000
   - Serve both API and frontend from a single port (required for autoscale)
   - Configure SSL and domain

**Important Note**: The FastAPI backend is configured to serve both:
- API endpoints at `/api/v1/*`
- Frontend static files (SPA) from `/`

This single-port architecture is required for Replit's Autoscale Deployments.

**Production Environment Variables in Replit:**

Add these in the Secrets panel:
- `DATABASE_URL` - Your production PostgreSQL URL (use `postgresql+asyncpg://` scheme)
- `REDIS_URL` - Your production Redis URL
- `BACKEND_CORS_ORIGINS` - Your production domain(s)
- `ENVIRONMENT=production`

**Port Configuration Requirements:**
- Autoscale deployments only support **one external port**
- The backend runs on internal port 8000 and maps to external port 80
- If you see port configuration errors, ensure only one port mapping exists in the `.replit` file

### Option 2: Docker Deployment

Use Docker for consistent deployment across platforms.

#### Build Images

```bash
# Build backend
docker build -f backend/Dockerfile -t tco-backend:latest .

# Build frontend (if serving separately)
docker build -f frontend/Dockerfile -t tco-frontend:latest ./frontend
```

#### Run with Docker Compose

For a complete stack deployment:

```bash
# Update docker-compose.yml with production values
docker compose -f docker-compose.prod.yml up -d
```

Create a `docker-compose.prod.yml`:

```yaml
version: "3.9"

services:
  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    command: uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - BACKEND_CORS_ORIGINS=${BACKEND_CORS_ORIGINS}
    depends_on:
      - postgres
      - redis
    restart: always

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

  redis:
    image: redis:7-alpine
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./frontend/dist:/usr/share/nginx/html
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
    depends_on:
      - backend
    restart: always

volumes:
  postgres_data:
```

### Option 3: Platform-as-a-Service (PaaS)

Deploy to cloud platforms like:

#### Heroku

```bash
# Install Heroku CLI
heroku login
heroku create tco-web-platform

# Set environment variables
heroku config:set DATABASE_URL=postgresql+asyncpg://...
heroku config:set REDIS_URL=redis://...
heroku config:set ENVIRONMENT=production

# Deploy
git push heroku main
```

#### DigitalOcean App Platform

1. Connect your repository
2. Configure build and run commands:
   - **Build**: `npm install && npm run build` (for frontend)
   - **Run**: `uvicorn backend.app.main:app --host 0.0.0.0 --port 8080`
3. Add environment variables in the dashboard
4. Deploy

#### AWS Elastic Beanstalk

1. Install EB CLI: `pip install awsebcli`
2. Initialize: `eb init -p python-3.11 tco-platform`
3. Create environment: `eb create tco-production`
4. Set environment variables via console or CLI
5. Deploy: `eb deploy`

## Database Setup

### Initialize Production Database

The application will automatically create tables on startup. However, for a fresh production database:

```bash
# Connect to your database and verify connectivity
python -c "
from backend.app.db.session import init_db
import asyncio
asyncio.run(init_db())
"
```

### Database Migrations

For schema changes, use SQLAlchemy with Alembic (recommended for future):

```bash
# Install Alembic
pip install alembic

# Initialize migrations
alembic init migrations

# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head
```

## SSL/HTTPS Configuration

### Using Let's Encrypt with Nginx

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal is configured automatically
```

### Nginx Configuration Example

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Frontend static files
    root /usr/share/nginx/html;
    index index.html;

    # SPA routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API proxy
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Post-Deployment

### Verification Checklist

- [ ] Health endpoint responds: `https://yourdomain.com/api/v1/health`
- [ ] Frontend loads and displays correctly
- [ ] Database connection successful
- [ ] Redis cache connection successful
- [ ] API endpoints return expected results
- [ ] CORS configured correctly for your domain
- [ ] SSL certificate valid and auto-renewing
- [ ] Error monitoring configured (Sentry, etc.)

### Smoke Tests

```bash
# Test health endpoint
curl https://yourdomain.com/api/v1/health

# Test vehicle list
curl https://yourdomain.com/api/v1/vehicles

# Test calculation (POST request)
curl -X POST https://yourdomain.com/api/v1/calculations \
  -H "Content-Type: application/json" \
  -d '{
    "vehicle_id": "BEV001",
    "scenario": "baseline",
    "purchase_method": "financed",
    "annual_kms": 50000
  }'
```

## Monitoring and Maintenance

### Logging

Configure structured logging for production:

```python
# In backend/app/main.py or config
import logging

logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}',
)
```

### Error Monitoring

Integrate Sentry for error tracking:

```bash
pip install sentry-sdk[fastapi]
```

```python
# In backend/app/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FastApiIntegration()],
    environment="production",
)
```

### Performance Monitoring

Monitor key metrics:
- API response times
- Database query performance
- Redis cache hit rates
- Memory and CPU usage
- Error rates

### Backup Strategy

#### Database Backups

For PostgreSQL:

```bash
# Automated daily backups
pg_dump -h host -U user -d dbname > backup_$(date +%Y%m%d).sql

# Restore from backup
psql -h host -U user -d dbname < backup_20251110.sql
```

#### Redis Persistence

Configure Redis persistence in `redis.conf`:

```
save 900 1
save 300 10
save 60 10000
```

### Updates and Maintenance

1. **Code Updates**: Deploy new versions with zero-downtime using blue-green deployment
2. **Dependency Updates**: Regular security updates via `pip-audit` and `npm audit`
3. **Database Migrations**: Test migrations in staging before production
4. **Cache Invalidation**: Clear Redis cache after data model changes if needed

## Security Checklist

- [ ] Environment variables secured and not committed to git
- [ ] Database credentials rotated regularly
- [ ] HTTPS enforced (no HTTP access)
- [ ] CORS restricted to known domains only
- [ ] SQL injection prevention via ORM
- [ ] Rate limiting configured (e.g., via Nginx or middleware)
- [ ] Security headers configured (HSTS, CSP, etc.)
- [ ] Regular dependency security scans
- [ ] Database backups encrypted
- [ ] Logs sanitized (no PII or secrets)

## Rollback Procedure

If deployment issues occur:

1. **Replit**: Use the built-in rollback feature in deployment settings
2. **Docker**: Revert to previous image tag
3. **Git**: Revert commit and redeploy
4. **Database**: Restore from backup if schema changes were problematic

## Support

For deployment issues or questions:
- Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
- Review application logs
- Contact the development team
