# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 5.1.x   | Yes |
| 5.0.x   | Yes |
| < 5.0   | Best-effort |

## Reporting a Vulnerability

Please **do not** open a public issue for security problems.

Contact the repository owner privately (GitHub profile / registered email) with:

- Description of the issue
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

We will acknowledge reports as quickly as possible and coordinate a fix and disclosure.

## Best Practices for Deployers

- Never commit `.env` or real API keys
- Rotate keys if leaked
- Keep dependencies updated
- Use strong `COLAB_WORKER_SECRET` and JWT secrets in production
- Restrict admin payment endpoints
