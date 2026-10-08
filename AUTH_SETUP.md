# Email OTP and Google Sign-In Setup

## 1. Install the updated packages

Run:

```text
pip install -r requirements.txt
```

Then run:

```text
python manage.py migrate
```

## 2. Email OTP

The registration flow now works like this:

1. The visitor fills in username, name, email, phone and password.
2. The account is kept in a temporary pending-registration record.
3. A 6-digit OTP is sent to the registered email.
4. The visitor enters the OTP on a separate verification page.
5. Only a correct OTP creates the real Django account.
6. The visitor can then log in normally.
7. An incorrect OTP does not create an account.
8. The verification page has a small **Send code again** button.
9. OTPs expire after 10 minutes and the code can be resent after a short cooldown.

For real email delivery, add these environment variables:

```text
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
```

For Gmail, use a Google **App Password**, not your normal Gmail password.

If these values are not supplied, Django uses its development console email backend. In that mode the OTP is printed in the terminal instead of being delivered to an inbox.

## 3. Google Sign-In

The login page includes a professional **Continue with Google** button.

To make it fully active:

1. Open Google Cloud Console.
2. Create or select a project.
3. Create an OAuth 2.0 Client ID for a Web Application.
4. Add this authorized redirect URI for the local project:

```text
http://127.0.0.1:8000/accounts/google/callback/
```

5. Add these environment variables:

```text
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://127.0.0.1:8000/accounts/google/callback/
```

The button uses Google's account chooser. If a matching email already exists, that account is signed in. Otherwise a new Django account is created using the verified Google email.

Never commit real email passwords, Google client secrets, or other credentials into the project or Git.
