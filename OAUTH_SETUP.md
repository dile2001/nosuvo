# OAuth 2.0 Setup Guide for NoSubvo

This guide will help you set up OAuth 2.0 authentication with Google, Microsoft, and Apple for the NoSubvo application.

## Prerequisites

- A domain name or local development environment
- Admin access to OAuth provider developer consoles

## 1. Google OAuth Setup

### Step 1: Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Google+ API and Google Identity API

### Step 2: Configure OAuth Consent Screen
1. Go to "APIs & Services" > "OAuth consent screen"
2. Choose "External" user type
3. Fill in required fields:
   - App name: NoSubvo
   - User support email: your-email@domain.com
   - Developer contact: your-email@domain.com
4. Add scopes: `email`, `profile`, `openid`
5. Add test users (for development)

### Step 3: Create OAuth Credentials
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. Choose "Web application"
4. Add authorized redirect URIs:
   - `http://localhost:5001/auth/callback` (development)
   - `https://yourdomain.com/auth/callback` (production)

### Step 4: Get Credentials
Copy the Client ID and Client Secret to your `.env` file:
```
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
```

## 2. Microsoft OAuth Setup

### Step 1: Register Application
1. Go to [Azure Portal](https://portal.azure.com/)
2. Navigate to "Azure Active Directory" > "App registrations"
3. Click "New registration"
4. Fill in:
   - Name: NoSubvo
   - Supported account types: "Accounts in any organizational directory and personal Microsoft accounts"
   - Redirect URI: `http://localhost:5001/auth/callback`

### Step 2: Configure Authentication
1. Go to "Authentication" in your app registration
2. Add platform: "Web"
3. Add redirect URIs:
   - `http://localhost:5001/auth/callback` (development)
   - `https://yourdomain.com/auth/callback` (production)
4. Enable "ID tokens" and "Access tokens"

### Step 3: Get Credentials
1. Go to "Overview" and copy the Application (client) ID
2. Go to "Certificates & secrets" > "New client secret"
3. Copy the client secret

Add to your `.env` file:
```
MICROSOFT_CLIENT_ID=your_microsoft_client_id_here
MICROSOFT_CLIENT_SECRET=your_microsoft_client_secret_here
```

## 3. Apple OAuth Setup

### Step 1: Create App ID
1. Go to [Apple Developer Console](https://developer.apple.com/account/)
2. Navigate to "Certificates, Identifiers & Profiles" > "Identifiers"
3. Click "+" to create new identifier
4. Choose "App IDs" > "App"
5. Fill in:
   - Description: NoSubvo
   - Bundle ID: com.yourcompany.nosuvo
6. Enable "Sign In with Apple" capability

### Step 2: Create Service ID
1. Go to "Identifiers" and create new "Services IDs"
2. Fill in:
   - Description: NoSubvo Web
   - Identifier: com.yourcompany.nosuvo.web
3. Enable "Sign In with Apple"
4. Configure domains and redirect URLs:
   - Primary App ID: select your App ID
   - Domains: yourdomain.com, localhost
   - Return URLs: `http://localhost:5001/auth/callback`, `https://yourdomain.com/auth/callback`

### Step 3: Create Private Key
1. Go to "Keys" and create new key
2. Enable "Sign In with Apple"
3. Download the `.p8` file
4. Note the Key ID

### Step 4: Get Team ID
1. Go to "Membership" to find your Team ID

Add to your `.env` file:
```
APPLE_CLIENT_ID=com.yourcompany.nosuvo.web
APPLE_TEAM_ID=your_team_id_here
APPLE_KEY_ID=your_key_id_here
APPLE_PRIVATE_KEY_PATH=/path/to/AuthKey_XXXXXXXXXX.p8
```

## 4. Environment Configuration

Create a `.env` file in your project root:

```bash
# Copy from env_template.txt and fill in your values
cp env_template.txt .env
```

Fill in your OAuth credentials:

```env
# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here

# Microsoft OAuth
MICROSOFT_CLIENT_ID=your_microsoft_client_id_here
MICROSOFT_CLIENT_SECRET=your_microsoft_client_secret_here

# Apple OAuth
APPLE_CLIENT_ID=your_apple_client_id_here
APPLE_TEAM_ID=your_apple_team_id_here
APPLE_KEY_ID=your_apple_key_id_here
APPLE_PRIVATE_KEY_PATH=/path/to/your/apple/private/key.p8

# OAuth Redirect URLs
OAUTH_REDIRECT_URI=http://localhost:5001/auth/callback
FRONTEND_URL=http://localhost:3000

# Flask Secret Key (generate a random string)
FLASK_SECRET_KEY=your_random_secret_key_here
```

## 5. Testing OAuth Integration

### Start the Application
```bash
# Backend
cd /Users/dile/labs/nosuvo
source venv/bin/activate
python backend.py

# Frontend (in another terminal)
cd frontend
npm start
```

### Test OAuth Providers
1. Open http://localhost:3000
2. Click "Login / Sign Up"
3. You should see OAuth provider buttons if configured correctly
4. Click on a provider to test the OAuth flow

### Verify OAuth Endpoints
```bash
# Check available providers
curl http://localhost:5001/auth/oauth/providers

# Test OAuth initiation (will redirect to provider)
curl http://localhost:5001/auth/oauth/google
```

## 6. Production Deployment

### Update Redirect URIs
Before deploying to production, update the redirect URIs in all OAuth provider configurations to use your production domain:

- Google: `https://yourdomain.com/auth/callback`
- Microsoft: `https://yourdomain.com/auth/callback`
- Apple: `https://yourdomain.com/auth/callback`

### Environment Variables
Update your production environment variables:
```env
OAUTH_REDIRECT_URI=https://yourdomain.com/auth/callback
FRONTEND_URL=https://yourdomain.com
```

### Security Considerations
1. Use HTTPS in production
2. Keep OAuth credentials secure
3. Regularly rotate client secrets
4. Monitor OAuth usage and errors
5. Implement rate limiting for OAuth endpoints

## 7. Troubleshooting

### Common Issues

1. **"Invalid redirect URI"**
   - Ensure redirect URIs match exactly in OAuth provider configuration
   - Check for trailing slashes and protocol (http vs https)

2. **"Client ID not found"**
   - Verify environment variables are set correctly
   - Restart the backend after changing environment variables

3. **Apple OAuth not working**
   - Ensure private key file exists and is readable
   - Check Team ID and Key ID are correct
   - Verify Bundle ID matches the configured one

4. **Frontend not receiving OAuth token**
   - Check browser console for errors
   - Verify CORS settings
   - Ensure frontend URL is correctly configured

### Debug Mode
Enable debug logging by setting:
```env
FLASK_DEBUG=True
```

This will show detailed error messages in the backend logs.

## 8. OAuth Flow Diagram

```
User clicks OAuth button
    ↓
Frontend redirects to /auth/oauth/{provider}
    ↓
Backend redirects to OAuth provider
    ↓
User authenticates with provider
    ↓
Provider redirects to /auth/callback with code
    ↓
Backend exchanges code for user info
    ↓
Backend creates/updates user and generates session token
    ↓
Backend redirects to frontend with token
    ↓
Frontend stores token and logs user in
```

## Support

For issues with OAuth setup:
1. Check the backend logs for detailed error messages
2. Verify all environment variables are set correctly
3. Test OAuth endpoints individually using curl
4. Check OAuth provider developer consoles for configuration issues
