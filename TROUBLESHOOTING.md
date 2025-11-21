# Troubleshooting Guide

Common issues and solutions for the TCO Web Platform.

## Table of Contents

- [Development Environment](#development-environment)
- [Frontend Issues](#frontend-issues)
- [Backend Issues](#backend-issues)
- [Database Issues](#database-issues)
- [API and Integration](#api-and-integration)
- [Performance Issues](#performance-issues)
- [Deployment Issues](#deployment-issues)

---

## Development Environment

### Docker Compose Fails to Start

**Symptoms:**
- `docker compose up` fails with port conflicts
- Services fail to connect to each other

**Solutions:**

1. **Port Conflicts:**
```bash
# Check what's using the ports
lsof -i :5000  # Frontend
lsof -i :8000  # Backend
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis

# Kill conflicting processes or change ports in docker-compose.yml
```

2. **Rebuild Containers:**
```bash
docker compose down
docker compose up --build
```

3. **Clean Everything:**
```bash
docker compose down -v  # Warning: Removes volumes/data
docker system prune -a
docker compose up --build
```

### Python Dependencies Not Installing

**Symptoms:**
- `pip install` fails with errors
- Module not found errors when running the app

**Solutions:**

1. **Update pip:**
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

2. **Use Virtual Environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Specific Package Failures:**
```bash
# For numpy/pandas compilation issues
pip install --no-cache-dir numpy pandas

# For asyncpg issues on some systems
pip install asyncpg --no-binary :all:
```

### Frontend Build Fails

**Symptoms:**
- `npm install` or `npm run build` fails
- TypeScript compilation errors

**Solutions:**

1. **Clean Install:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

2. **Node Version:**
```bash
# Ensure Node.js 20+
node --version

# Use nvm to switch versions
nvm install 20
nvm use 20
```

3. **TypeScript Errors:**
```bash
# Regenerate shared data files
python scripts/generate_vehicle_catalog_ts.py

# Check types
npm run typecheck
```

---

## Frontend Issues

### White Screen / App Won't Load

**Symptoms:**
- Browser shows blank white screen
- Console shows errors

**Solutions:**

1. **Check Browser Console:**
```
Press F12 → Console tab
Look for errors related to:
- Network requests failing
- Module not found
- CORS errors
```

2. **Verify Backend is Running:**
```bash
curl http://localhost:8000/api/v1/health
```

3. **Check Environment Variables:**
```bash
# In frontend/.env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

4. **Clear Browser Cache:**
- Hard refresh: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
- Clear site data in DevTools → Application → Clear storage

### Calculation Results Not Appearing

**Symptoms:**
- Wizard completes but no results shown
- Error toast appears

**Solutions:**

1. **Check Network Requests:**
```
F12 → Network tab → Filter by XHR
Look for failed API calls to /sessions or console errors thrown during calculation
```

2. **Verify Form Data:**
```javascript
// Check Zustand state in console
window.localStorage.getItem('tco-wizard-storage')
```

3. **Backend Logs:**
```bash
# Check backend terminal for errors
# Look for validation errors or calculation failures
```

### Session Not Persisting

**Symptoms:**
- Session ID not saved
- Data lost on page refresh

**Solutions:**

1. **Check Database Connection:**
```bash
# In backend logs, verify:
# "Database initialized successfully"
```

2. **Redis Connection:**
```bash
# Test Redis connectivity
redis-cli ping
# Should respond: PONG
```

3. **Check Browser Storage:**
```
F12 → Application → Local Storage
Verify tco-wizard-storage exists
```

---

## Backend Issues

### FastAPI Won't Start

**Symptoms:**
- `uvicorn` command fails
- Import errors on startup

**Solutions:**

1. **Check Python Path:**
```bash
export PYTHONPATH=$(pwd)
uvicorn backend.app.main:app --reload
```

2. **Verify Dependencies:**
```bash
pip install -r requirements.txt
python -c "import backend.app.main"
```

3. **Database Connection:**
```bash
# Verify DATABASE_URL is set
echo $DATABASE_URL

# Test database connectivity
python -c "
from backend.app.db.session import init_db
import asyncio
asyncio.run(init_db())
"
```

### Slow API Responses

**Symptoms:**
- API requests take > 2 seconds
- Timeout errors

**Solutions:**

1. **Enable Caching:**
```python
# In backend/.env or environment
CACHE_RESULTS=true
```

2. **Check Database Queries:**
```bash
# Enable SQL logging
# In backend/app/core/config.py, temporarily add:
# echo=True to create_async_engine
```

3. **Redis Performance:**
```bash
redis-cli INFO stats
# Check keyspace hits/misses ratio
```

### CORS Errors

**Symptoms:**
- Browser console shows "CORS policy" errors
- Frontend can't connect to backend

**Solutions:**

1. **Update CORS Origins:**
```python
# In backend/.env or backend/app/core/config.py
BACKEND_CORS_ORIGINS=http://localhost:5000,http://127.0.0.1:5000
```

2. **Verify Middleware:**
```python
# In backend/app/main.py, ensure CORSMiddleware is configured
```

3. **Development Workaround:**
```bash
# Start backend with all origins allowed (dev only!)
# In config temporarily: allow_origins=["*"]
```

---

## Database Issues

### Database Connection Failed

**Symptoms:**
- "Connection refused" errors
- SQLAlchemy connection errors

**Solutions:**

1. **PostgreSQL Not Running:**
```bash
# Check PostgreSQL status
docker ps | grep postgres
# Or if local install:
sudo systemctl status postgresql
```

2. **Wrong Database URL:**
```bash
# Verify format
# Correct: postgresql+asyncpg://user:password@host:5432/dbname
# Wrong: postgres://... (missing async driver)

# Test connection
python -c "
import asyncpg
import asyncio
async def test():
    conn = await asyncpg.connect('postgresql://user:password@host/db')
    await conn.close()
asyncio.run(test())
"
```

3. **Firewall/Network:**
```bash
# Test port connectivity
telnet localhost 5432
# Or
nc -zv localhost 5432
```

### Migration/Schema Issues

**Symptoms:**
- Table doesn't exist errors
- Column not found errors

**Solutions:**

1. **Reinitialize Database:**
```bash
# Drops and recreates tables (WARNING: Loses data)
python -c "
from backend.app.db.session import init_db
import asyncio
asyncio.run(init_db())
"
```

2. **Check Database State:**
```sql
-- Connect to database
psql -h localhost -U tco_user -d tco_db

-- List tables
\dt

-- Check schema
\d session_records
```

### Redis Connection Issues

**Symptoms:**
- Session caching not working
- Redis connection errors in logs

**Solutions:**

1. **Redis Not Running:**
```bash
docker ps | grep redis
# Or
sudo systemctl status redis
```

2. **Test Connection:**
```bash
redis-cli -h localhost -p 6379 ping
```

3. **Disable Redis (Fallback):**
```python
# In backend/.env
REDIS_URL=
# App will work without caching
```

---

## API and Integration

### 404 Not Found for API Routes

**Symptoms:**
- `/api/v1/vehicles` returns 404
- Routes not registered

**Solutions:**

1. **Check API Prefix:**
```bash
# Routes should be:
# http://localhost:8000/api/v1/health
# NOT: http://localhost:8000/health
```

2. **Verify Router Registration:**
```python
# In backend/app/main.py
app.include_router(api_router)
```

3. **Check FastAPI Docs:**
```
Visit: http://localhost:8000/docs
See all registered routes
```

### Parity Test Failures

**Symptoms:**
- Vitest fixtures (`verification.test.ts`) report differences against expected values
- Calculation differences > 1%

**Solutions:**

1. **Regenerate shared data:**
```bash
python scripts/generate_vehicle_catalog_ts.py
cd frontend
npm run test -- verification.test.ts
```

2. **Inspect failing cases:**
```bash
# Add a focused test or log the failing vehicle/scenario inside the calculator
npm run test -- verification.test.ts --runInBand
```

3. **Update fixtures intentionally (only when business logic changes):**
   - Confirm the new outputs are correct and stable.
   - Update `shared/calculator/verification_data.json` with the new expected values.

---

## Performance Issues

### Slow Calculation Times

**Symptoms:**
- Calculations take > 1 second
- UI feels sluggish

**Solutions:**

1. **Use Client-Side Calculator:**
```typescript
// Verify shared calculator is being used
// Check frontend/src/hooks/useCalculations.ts
```

2. **Enable Result Caching:**
```python
# backend/.env
CACHE_RESULTS=true
```

3. **Profile Python Code:**
```bash
pip install line-profiler
python -m line_profiler backend/app/services/sessions.py
```

### High Memory Usage

**Symptoms:**
- Backend using > 500MB RAM
- Out of memory errors

**Solutions:**

1. **Check Cache Size:**
```python
# In backend/app/core/cache.py
# Limit cache size or implement LRU
```

2. **Database Connection Pool:**
```python
# In backend/app/db/session.py
# Adjust pool_size and max_overflow
```

---

## Deployment Issues

### Production Build Fails

**Symptoms:**
- `npm run build` fails
- Missing environment variables

**Solutions:**

1. **Environment Variables:**
```bash
# Ensure all required vars are set
cd frontend
cat .env.production
VITE_API_BASE_URL=https://yourapi.com/api/v1
```

2. **Build Locally First:**
```bash
cd frontend
npm run build
# Check frontend/dist/ directory exists
```

### SSL/HTTPS Issues

**Symptoms:**
- Mixed content warnings
- Certificate errors

**Solutions:**

1. **Force HTTPS:**
```nginx
# In nginx.conf
return 301 https://$server_name$request_uri;
```

2. **Update API URLs:**
```bash
# Ensure frontend uses https://
VITE_API_BASE_URL=https://api.yourdomain.com/api/v1
```

### Database Migration Errors in Production

**Symptoms:**
- Schema mismatch errors
- Table not found after deployment

**Solutions:**

1. **Manual Migration:**
```bash
# SSH into production server
python -c "
from backend.app.db.session import init_db
import asyncio
asyncio.run(init_db())
"
```

2. **Backup First:**
```bash
pg_dump -h host -U user dbname > backup.sql
```

---

## Getting Help

If your issue isn't covered here:

1. **Check Logs:**
   - Backend: Console output from `uvicorn`
   - Frontend: Browser DevTools Console
   - Database: PostgreSQL logs
   - Nginx: `/var/log/nginx/error.log`

2. **Enable Debug Mode:**
```python
# backend/.env
DEBUG=true
LOG_LEVEL=DEBUG
```

3. **Minimal Reproduction:**
   - Isolate the issue
   - Create a minimal test case
   - Document steps to reproduce

4. **Contact Support:**
   - Include error messages
   - Share relevant logs
   - Describe what you've tried

## Common Error Messages

| Error | Meaning | Solution |
|-------|---------|----------|
| `ModuleNotFoundError: No module named 'backend'` | PYTHONPATH not set | `export PYTHONPATH=$(pwd)` |
| `sqlalchemy.exc.OperationalError: could not connect` | Database not accessible | Check DATABASE_URL and PostgreSQL status |
| `Redis connection error` | Redis not running | Start Redis or disable in config |
| `CORS policy: No 'Access-Control-Allow-Origin'` | CORS misconfigured | Update BACKEND_CORS_ORIGINS |
| `404: Not Found` for API | Wrong API prefix | Use `/api/v1/` prefix |
| `Module parse failed: Unexpected token` | Frontend build issue | Clear cache, rebuild |
| `Calculation result mismatch` | TS/Python parity issue | Regenerate snapshots |
