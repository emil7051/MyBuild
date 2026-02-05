# Security Policy

This document outlines the security practices for the TCO Web Platform, including vulnerability management and reporting procedures.

## Dependency Vulnerability Scanning

### Automated Scanning

The project uses automated dependency vulnerability scanning in CI/CD:

- **Python dependencies**: Scanned using `pip-audit` on every push and PR to main
- **Frontend dependencies**: Scanned using `npm audit` on every push and PR to main
- **Scheduled scans**: Weekly scans run on Mondays at 9am UTC to detect newly disclosed vulnerabilities

### Fail Policy

| Stack | Severity Threshold | Action |
|-------|-------------------|--------|
| Python | Any vulnerability | CI fails (strict mode) |
| Frontend | High or Critical | CI fails |
| Frontend | Moderate or Low | Warning only (logged) |

### Resolution Process

When vulnerabilities are detected:

1. **Review**: Check the vulnerability details in the CI job logs
2. **Assess**: Determine if the vulnerability affects production code
3. **Remediate**: Update to a patched version if available
4. **Mitigate**: If no patch exists, implement compensating controls

### Ignoring Vulnerabilities

For false positives or accepted risks, document the justification:

#### Python (pip-audit)

Create a file `.pip-audit-ignore.yml` if needed:

```yaml
# Example: Ignore specific vulnerability
vulnerabilities:
  - id: PYSEC-2024-XXXXX
    reason: "False positive - affected code path not used in this project"
    expires: 2024-12-31  # Re-review date
```

#### Frontend (npm)

Use `.nsprc` or `npm audit` resolution in `package.json`:

```json
{
  "overrides": {
    "vulnerable-package": "^2.0.0"
  }
}
```

Document any accepted risks in `docs/security-exceptions.md` with:
- Vulnerability ID
- Affected package and version
- Risk assessment
- Mitigating controls
- Review date

## Reporting Security Vulnerabilities

If you discover a security vulnerability in this project:

1. **Do not** open a public GitHub issue
2. Email the maintainers directly (see CODEOWNERS or repository settings)
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We aim to acknowledge reports within 48 hours and provide a fix timeline within 7 days.

## Security Best Practices

### Backend

- Input validation on all API endpoints
- Parameterized queries (SQLAlchemy ORM)
- Rate limiting on session/analytics endpoints
- Session access for read/update requires `sessionId` + `X-Session-Secret`
- Analytics endpoint requires `ANALYTICS_API_KEY` and is disabled if unset
- Path traversal protection for static file serving
- CORS configuration restricts allowed origins

### Frontend

- Input sanitization in forms
- Content Security Policy headers (when deployed)
- Session IDs and session secrets are stored in localStorage for resume; no PII is stored in localStorage by the frontend

### Data Layer

- Database migrations via Alembic (no manual schema changes)
- Indexes on frequently queried columns
- Prepared statements prevent SQL injection

## Security-Related Configuration

### Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:5000` |
| `RATE_LIMIT_*` | Rate limiting thresholds | See `backend/app/core/config.py` |
| `DATABASE_URL` | Database connection | SQLite in dev |

### Sensitive Data Handling

- Session data may include optional operator profile fields if supplied via API; session endpoints are unauthenticated by default, so avoid storing sensitive data unless access control is added
- Analytics data is aggregated; individual sessions are not publicly queryable
- No plaintext secrets in codebase (use environment variables)
