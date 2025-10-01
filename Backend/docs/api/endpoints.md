# Luna Server API Endpoints

## 🌐 Overview

Luna Server provides REST API endpoints for webhook handling, health monitoring, and basic administrative functions. This document covers all currently implemented endpoints with examples and usage guidelines.

## 📋 Base Information

- **Base URL**: `https://your-domain.com` (or `http://localhost:8000` for local development)
- **Content-Type**: `application/json` for POST requests
- **Authentication**: Currently webhook-based validation for channels

## 🏥 Health & Status Endpoints

### GET /health

Check the overall health and status of the Luna Server.

**Response:**
```json
{
  "status": "healthy",
  "service": "Luna Server",
  "startup_status": {
    "telegram_webhook_registered": true,
    "startup_complete": true,
    "internet_connectivity": true,
    "errors": []
  }
}
```

**Status Values:**
- `healthy` - Startup completed successfully
- `degraded` - Startup not yet completed or has errors

### GET /

Basic root endpoint that returns a simple greeting.

**Response:**
```json
{
  "Hello World, from Luna!"
}
```

## 📱 Channel Webhook Endpoints

### POST /webhook/telegram

Handles incoming messages from Telegram Bot API.

**Headers:**
- `X-Telegram-Bot-Api-Secret-Token`: Webhook secret for validation

**Request Body:**
Telegram webhook update object as defined by [Telegram Bot API](https://core.telegram.org/bots/api#update).

**Example:**
```json
{
  "update_id": 123456789,
  "message": {
    "message_id": 1,
    "from": {
      "id": 123456789,
      "is_bot": false,
      "first_name": "John",
      "username": "johndoe"
    },
    "chat": {
      "id": 123456789,
      "first_name": "John",
      "username": "johndoe",
      "type": "private"
    },
    "date": 1640995200,
    "text": "Hello Luna"
  }
}
```

**Response:**
```json
{
  "ok": true,
  "scheduled": true
}
```

**Error Response:**
```json
{
  "ok": false,
  "error": "Invalid webhook secret."
}
```

### POST /webhook/whatsapp

Handles incoming messages from WhatsApp Business API.

**Headers:**
- `X-Hub-Signature-256`: Webhook signature for validation

**Request Body:**
WhatsApp webhook payload as defined by [WhatsApp Business API](https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks).

**Example:**
```json
{
  "object": "whatsapp_business_account",
  "entry": [
    {
      "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
      "changes": [
        {
          "value": {
            "messaging_product": "whatsapp",
            "metadata": {
              "display_phone_number": "15550559999",
              "phone_number_id": "PHONE_NUMBER_ID"
            },
            "messages": [
              {
                "from": "16505551234",
                "id": "wamid.ID",
                "timestamp": "1640995200",
                "text": {
                  "body": "Hello Luna"
                },
                "type": "text"
              }
            ]
          },
          "field": "messages"
        }
      ]
    }
  ]
}
```

**Response:**
```json
{
  "ok": true,
  "scheduled": true
}
```

### GET /webhook/whatsapp

WhatsApp webhook verification endpoint.

**Query Parameters:**
- `hub.mode`: Should be "subscribe"
- `hub.verify_token`: Verification token
- `hub.challenge`: Challenge string to echo back

**Example Request:**
```
GET /webhook/whatsapp?hub.mode=subscribe&hub.verify_token=your_token&hub.challenge=1234567890
```

**Response:**
Returns the challenge number if verification succeeds, or 403 if it fails.

## 💳 Payment Webhook Endpoints

### POST /razorpay/webhook

Handles payment status updates from Razorpay.

**Response:**
```json
{
  "ok": true,
  "message": "Payment webhook processed successfully"
}
```

## 🔧 Administrative Endpoints

### POST /admin/retry-telegram-webhook

Manually retry Telegram webhook registration.

**Response:**
```json
{
  "ok": true,
  "message": "Telegram webhook registered successfully"
}
```

**Error Response:**
```json
{
  "ok": false,
  "message": "Failed to register Telegram webhook",
  "errors": ["Connection timeout", "Invalid bot token"]
}
```

### POST /admin/check-internet-connectivity

Test internet connectivity with detailed diagnostics.

**Response:**
```json
{
  "ok": true,
  "overall_status": "healthy",
  "summary": "2/2 tests passed",
  "test_results": [
    {
      "test": "Basic HTTP connectivity",
      "status": "✅ PASSED",
      "endpoint": "https://httpbin.org/get",
      "response_time": "0.45s",
      "status_code": 200
    }
  ]
}
```

## 🔍 Error Handling

### Standard Error Response Format

All endpoints return errors in a consistent format:

```json
{
  "ok": false,
  "error": "Error description",
  "details": {
    "error_code": "VALIDATION_ERROR",
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_123456789"
  }
}
```

### HTTP Status Codes

| Status Code | Description | Usage |
|-------------|-------------|-------|
| 200 | OK | Successful request |
| 400 | Bad Request | Invalid request data |
| 403 | Forbidden | Authentication/authorization failed |
| 404 | Not Found | Endpoint not found |
| 500 | Internal Server Error | Server-side error |

### Common Error Scenarios

#### Webhook Validation Failed
```json
{
  "ok": false,
  "error": "Invalid webhook signature"
}
```
**Status Code:** 403

#### Invalid JSON Payload
```json
{
  "ok": false,
  "error": "Invalid JSON in request body"
}
```
**Status Code:** 400

#### Missing Required Headers
```json
{
  "ok": false,
  "error": "Missing required header: X-Telegram-Bot-Api-Secret-Token"
}
```
**Status Code:** 400

#### Server Error
```json
{
  "ok": false,
  "error": "Internal server error occurred"
}
```
**Status Code:** 500

## 🧪 Testing Endpoints

### Using cURL

#### Health Check
```bash
curl -X GET http://localhost:8000/health
```

#### Simulate Telegram Webhook (for testing)
```bash
curl -X POST http://localhost:8000/webhook/telegram \
  -H "Content-Type: application/json" \
  -H "X-Telegram-Bot-Api-Secret-Token: your_secret" \
  -d '{
    "update_id": 123456789,
    "message": {
      "message_id": 1,
      "from": {"id": 123456789, "first_name": "Test"},
      "chat": {"id": 123456789, "type": "private"},
      "date": 1640995200,
      "text": "Hello Luna"
    }
  }'
```

#### Check Internet Connectivity
```bash
curl -X POST http://localhost:8000/admin/check-internet-connectivity
```

### Using Python Requests

```python
import requests

# Health check
response = requests.get("http://localhost:8000/health")
print(response.json())

# Simulate webhook
webhook_data = {
    "update_id": 123456789,
    "message": {
        "message_id": 1,
        "from": {"id": 123456789, "first_name": "Test"},
        "chat": {"id": 123456789, "type": "private"},
        "date": 1640995200,
        "text": "Hello Luna"
    }
}

response = requests.post(
    "http://localhost:8000/webhook/telegram",
    json=webhook_data,
    headers={"X-Telegram-Bot-Api-Secret-Token": "your_secret"}
)
print(response.json())
```

### Using JavaScript/Node.js

```javascript
// Health check
const healthResponse = await fetch('http://localhost:8000/health');
const healthData = await healthResponse.json();
console.log(healthData);

// Simulate webhook
const webhookData = {
    update_id: 123456789,
    message: {
        message_id: 1,
        from: { id: 123456789, first_name: "Test" },
        chat: { id: 123456789, type: "private" },
        date: 1640995200,
        text: "Hello Luna"
    }
};

const webhookResponse = await fetch('http://localhost:8000/webhook/telegram', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-Telegram-Bot-Api-Secret-Token': 'your_secret'
    },
    body: JSON.stringify(webhookData)
});

const result = await webhookResponse.json();
console.log(result);
```

## 🔒 Security Considerations

### Webhook Validation

All webhook endpoints implement proper signature validation:

1. **Telegram**: Uses `X-Telegram-Bot-Api-Secret-Token` header
2. **WhatsApp**: Uses `X-Hub-Signature-256` header with HMAC-SHA256
3. **Razorpay**: Uses `X-Razorpay-Signature` header with HMAC-SHA256

### Rate Limiting

Rate limiting is not currently implemented.

### HTTPS Requirements

- All production webhooks must use HTTPS
- Webhook URLs must be publicly accessible
- SSL certificates must be valid

## 📊 Monitoring and Observability

### Request Logging

All requests are logged with:
- Request ID
- Timestamp
- Source IP
- Endpoint
- Response status
- Processing time

### Metrics Collection

Available metrics:
- Request count per endpoint
- Response time percentiles
- Error rate by endpoint
- Webhook validation success/failure rates

### Health Monitoring

The `/health` endpoint provides comprehensive status information:
- Database connectivity
- External service availability
- Webhook registration status
- System resource usage


---

This API documentation covers all currently implemented Luna Server endpoints. The server provides webhook endpoints for messaging platforms, basic health monitoring, and administrative functions for debugging and maintenance.
