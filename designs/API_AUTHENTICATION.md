# PsySuite Web API Authentication

## Overview

The PsySuite Web API uses API key authentication to secure endpoints used by the PsySuite Android application. This ensures that only authorized PsySuite instances can upload experiment data and access test configurations.

## API Key Configuration

### Server Configuration

By default, the API key uses the same value as `SECRET_KEY`. You can optionally set a different API key in the `.env` file:

```bash
# Flask secret key (also used as API key by default)
SECRET_KEY=psysuite-web-manager-2024-secure-key-change-in-production

# Optional: Set a different API key (if not set, uses SECRET_KEY)
# PSYSUITE_API_KEY=different-api-key-if-needed
```

**Important**: Change the default SECRET_KEY in production!

### Android App Configuration

In your PsySuite Android app, set the `webApiKey` to match the server configuration:

```kotlin
// In your Android app configuration
val webApiKey = "psysuite-web-manager-2024-secure-key-change-in-production"
```

## Protected Endpoints

The following endpoints require API key authentication:

### Upload Endpoints
- `POST /api/upload/experiment` - Upload experiment data
- `POST /api/upload/validate` - Validate experiment data before upload

### Test Endpoints  
- `GET /api/tests/public` - Get available tests for PsySuite app

### Info Endpoints
- `GET /api/upload/auth-info` - Get authentication information (for debugging)

## Authentication Methods

The API key can be provided in several ways:

### 1. X-API-Key Header (Recommended)
```bash
curl -H "X-API-Key: your-api-key" http://localhost:5000/api/tests/public
```

### 2. Authorization Bearer Header
```bash
curl -H "Authorization: Bearer your-api-key" http://localhost:5000/api/tests/public
```

### 3. Query Parameter
```bash
curl "http://localhost:5000/api/tests/public?api_key=your-api-key"
```

### 4. JSON Body (for POST requests)
```bash
curl -X POST -H "Content-Type: application/json" \
     -d '{"api_key": "your-api-key", "other": "data"}' \
     http://localhost:5000/api/upload/validate
```

## Android Implementation

In your Android app's network client, add the API key to requests:

```kotlin
// Using OkHttp interceptor
class ApiKeyInterceptor(private val apiKey: String) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val request = chain.request().newBuilder()
            .addHeader("X-API-Key", apiKey)
            .build()
        return chain.proceed(request)
    }
}

// Add to your HTTP client
val client = OkHttpClient.Builder()
    .addInterceptor(ApiKeyInterceptor(webApiKey))
    .build()
```

## Error Responses

### Missing API Key (401)
```json
{
    "error": "API key required",
    "message": "Please provide API key in X-API-Key header, Authorization Bearer header, or api_key parameter"
}
```

### Invalid API Key (401)
```json
{
    "error": "Invalid API key", 
    "message": "The provided API key is not valid"
}
```

## Testing

Use the provided test script to verify API key authentication:

```bash
source venv/bin/activate
python3 test_api_auth.py
```

## Security Notes

1. **Change the default API key** in production environments
2. **Use HTTPS** in production to protect the API key in transit
3. **Rotate API keys** periodically for better security
4. **Monitor API usage** through the access logs
5. **Keep API keys secure** in your Android app (consider using Android Keystore)

## Debugging

To check API key configuration:

```bash
curl http://localhost:5000/api/upload/auth-info
```

This will show authentication requirements and configuration status (without revealing the actual key).