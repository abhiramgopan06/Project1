# Deployment checklist

- Set `DJANGO_DEBUG=False`, a unique `DJANGO_SECRET_KEY`, and `DJANGO_ALLOWED_HOSTS`.
- Configure production PostgreSQL and private environment variables.
- Set secure session/CSRF cookies and HTTPS behind a correctly configured proxy.
- Configure real SMTP email and test OTP/order email delivery.
- Configure Razorpay test keys first; verify signatures server-side and use webhooks for final payment state.
- Run migrations, `python manage.py check --deploy`, and automated tests.
- Configure static collection, persistent media storage, backups, logging, monitoring and error reporting.
- Never commit `.env`, credentials, database dumps, or customer data.
