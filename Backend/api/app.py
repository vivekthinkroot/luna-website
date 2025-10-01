"""
Main FastAPI application for Luna.
Receives all inbound messages and provides health check endpoint.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Optional

import httpx
from fastapi import FastAPI, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.middleware import AccessLogMiddleware
from channels.telegram import (
    TelegramWebhookHandler,
    register_telegram_webhook,
)
from channels.whatsapp import WhatsAppWebhookHandler
from config.settings import get_settings
from services.channels import ChannelsService
from services.payments import PaymentsService
from utils.logger import get_logger
from utils.models import CanonicalRequestMessage
from api.routers.profile import router as profile_router
from api.routers.auth import router as auth_router
from api.routers.kundli import router as kundli_router
from api.routers.kundli_generate import router as kundli_generate_router
from api.routers.payments import router as payments_router
# Background polling tasks removed - status checking now handled by redirect page

# Initialize logger
logger = get_logger()

# Simple startup status
startup_status = {
    "telegram_webhook_registered": False,
    "startup_complete": False,
    "errors": [],
    "internet_connectivity": False
}


async def check_internet_connectivity():
    """Check if the app can reach the internet by making a simple HTTP request."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("https://httpbin.org/get")
            if response.status_code == 200:
                startup_status["internet_connectivity"] = True
                logger.info("✅ Internet connectivity check passed")
            else:
                startup_status["internet_connectivity"] = False
                error_msg = f"Internet connectivity check failed with status {response.status_code}"
                logger.warning(f"⚠️ {error_msg}")
                startup_status["errors"].append(error_msg)
    except Exception as e:
        error_msg = f"Internet connectivity check failed: {str(e)}"
        logger.warning(f"⚠️ {error_msg}")
        startup_status["errors"].append(error_msg)
        startup_status["internet_connectivity"] = False


async def register_telegram_webhook_safely():
    """Register Telegram webhook with simple error handling."""
    try:
        await register_telegram_webhook()
        startup_status["telegram_webhook_registered"] = True
        logger.info("✅ Telegram webhook registered successfully")
    except Exception as e:
        error_msg = f"Telegram webhook registration failed: {str(e)}"
        logger.warning(f"⚠️ {error_msg}")
        startup_status["errors"].append(error_msg)
        # Don't crash the app, just log the error


# App startup lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):    
    try:
        # Mark startup as complete first
        startup_status["startup_complete"] = True
        logger.info("🚀 Luna Server startup completed successfully")
        
        # Check internet connectivity in background
        asyncio.create_task(check_internet_connectivity())
        
        # Register webhook in background (non-blocking)
        asyncio.create_task(register_telegram_webhook_safely())
        
        # Payment monitoring background tasks removed
        # Status checking is now handled by the redirect page (/kundli/redirect)
        # which calls /payments/check-status endpoint directly
        logger.info("✅ Payment monitoring via redirect page (no background polling)")
        
    except Exception as e:
        error_msg = f"Critical startup error: {str(e)}"
        logger.error(f"❌ {error_msg}")
        startup_status["errors"].append(error_msg)
        startup_status["startup_complete"] = False
        # Don't crash the app, log the error and continue
    
    yield
    
    logger.info("🔄 Luna Server shutting down...")

app = FastAPI(title="Luna Server", version="0.1.0", lifespan=lifespan, docs_url="/luna-server/v1")

# Configure CORS (allow all origins for now)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom access logging middleware
app.add_middleware(AccessLogMiddleware)

settings = get_settings()

telegram_webhook_path = getattr(settings.telegram, "webhook_path")
if not telegram_webhook_path.startswith("/"):
    telegram_webhook_path = "/" + telegram_webhook_path

whatsapp_webhook_path = getattr(settings.whatsapp, "webhook_path")
if not whatsapp_webhook_path.startswith("/"):
    whatsapp_webhook_path = "/" + whatsapp_webhook_path

telegram_handler = TelegramWebhookHandler()
whatsapp_handler = WhatsAppWebhookHandler()
channels_service = ChannelsService()
payments_service = PaymentsService()


@app.post(telegram_webhook_path, tags=["Telegram"])
async def telegram_webhook(
    request: Request, x_telegram_bot_api_secret_token: str = Header(None)
):
    body = await request.body()
    headers = dict(request.headers)
    # Validate webhook secret
    if not telegram_handler.validate_webhook(headers, body.decode()):
        logger.warning("Invalid Telegram webhook secret.")
        return JSONResponse(
            status_code=403,
            content={"ok": False, "error": "Invalid webhook secret."},
        )
    try:
        payload = await request.json()
        logger.debug(f"Received Telegram webhook call: {payload}")

        canonical_msg: CanonicalRequestMessage = (
            await telegram_handler.parse_incoming_message(payload)
        )
        # Non-blocking enqueue; actual processing is scheduled inside service
        await channels_service.enqueue_incoming_message(canonical_msg)
        return JSONResponse(content={"ok": True, "scheduled": True})
    except Exception as e:
        logger.error(f"Error processing Telegram webhook: {e}")
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})


@app.post(whatsapp_webhook_path, tags=["WhatsApp"])
async def whatsapp_webhook(request: Request):
    body = await request.body()
    headers = dict(request.headers)
    if not whatsapp_handler.validate_webhook(headers, body.decode()):
        logger.warning("Invalid WhatsApp webhook signature.")
        return JSONResponse(
            status_code=403,
            content={"error": "Invalid webhook signature"},
        )
    try:
        payload = await request.json()
        logger.debug(f"Received WhatsApp webhook call: {payload}")
        canonical_msg: Optional[CanonicalRequestMessage] = (
            await whatsapp_handler.parse_incoming_message(payload)
        )

        # Handle status updates (when parse_incoming_message returns None)
        if canonical_msg is None:
            logger.debug("WhatsApp status update processed, no further action needed")
            return JSONResponse(content={"success": True})

        # Non-blocking enqueue; actual processing is scheduled inside service
        await channels_service.enqueue_incoming_message(canonical_msg)
        return JSONResponse(content={"ok": True, "scheduled": True})
    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get(whatsapp_webhook_path, tags=["WhatsApp"])
async def whatsapp_webhook_verify(request: Request):
    """WhatsApp webhook verification endpoint"""
    query_params = request.query_params
    mode = query_params.get("hub.mode")
    token = query_params.get("hub.verify_token")
    challenge = query_params.get("hub.challenge")

    if mode == "subscribe" and token == settings.whatsapp.webhook_verify_token:
        logger.info("WhatsApp webhook verified successfully")
        return int(challenge) if challenge else 0
    else:
        logger.warning("WhatsApp webhook verification failed")
        return JSONResponse(status_code=403, content={"error": "Forbidden"})


@app.post("/webhook", tags=["Payments"])
async def razorpay_webhook(request: Request, x_razorpay_signature: str = Header(None)):
    """
    Razorpay webhook endpoint for payment status updates with HMAC verification.
    Handles payment status changes from Razorpay with signature verification.
    """
    try:
        # Get raw request body for HMAC verification
        body = await request.body()
        
        # Verify HMAC signature
        if not payments_service.verify_razorpay_signature(body, x_razorpay_signature):
            logger.warning("Invalid Razorpay webhook signature")
            return JSONResponse(
                status_code=403,
                content={"ok": False, "error": "Invalid signature"}
            )
        
        # Parse JSON payload
        payload = await request.json()
        logger.info(f"Received verified Razorpay webhook: {payload}")

        # Delegate webhook processing to PaymentsService
        result = await payments_service.process_razorpay_webhook(payload)
        
        if result["ok"]:
            return JSONResponse(content=result)
        else:
            return JSONResponse(status_code=400, content=result)

    except Exception as e:
        logger.error(f"Error processing Razorpay webhook: {e}")
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})


@app.get("/health")
def health_check():
    """Health check endpoint for container orchestration"""
    return {
        "status": "healthy" if startup_status["startup_complete"] else "degraded",
        "service": "Luna Server",
        "startup_status": startup_status
    }


@app.get("/")
def read_root():
    return {"Hello World, from Luna!"}


@app.post("/admin/retry-telegram-webhook")
async def retry_telegram_webhook():
    """Admin endpoint to manually retry Telegram webhook registration."""
    try:
        logger.info("🔄 Manual retry: Attempting to register Telegram webhook...")
        await register_telegram_webhook_safely()
        
        if startup_status["telegram_webhook_registered"]:
            return {"ok": True, "message": "Telegram webhook registered successfully"}
        else:
            return {"ok": False, "message": "Failed to register Telegram webhook", "errors": startup_status["errors"]}
            
    except Exception as e:
        error_msg = f"Manual retry error: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return {"ok": False, "message": "Error during manual retry", "error": str(e)}


@app.post("/admin/check-internet-connectivity")
async def check_internet_connectivity_admin():
    """Admin endpoint to manually test internet connectivity with detailed diagnosis."""
    try:
        logger.info("🌐 Manual test: Checking internet connectivity...")
        
        # Test multiple endpoints for comprehensive diagnosis
        test_results = []
        
        # Test 1: Basic HTTP connectivity
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get("https://httpbin.org/get")
                if response.status_code == 200:
                    test_results.append({
                        "test": "Basic HTTP connectivity",
                        "status": "✅ PASSED",
                        "endpoint": "https://httpbin.org/get",
                        "response_time": f"{response.elapsed.total_seconds():.2f}s",
                        "status_code": response.status_code
                    })
                else:
                    test_results.append({
                        "test": "Basic HTTP connectivity",
                        "status": "❌ FAILED",
                        "endpoint": "https://httpbin.org/get",
                        "status_code": response.status_code,
                        "error": f"HTTP {response.status_code}"
                    })
        except Exception as e:
            test_results.append({
                "test": "Basic HTTP connectivity",
                "status": "❌ FAILED",
                "endpoint": "https://httpbin.org/get",
                "error": str(e)
            })
        
        # Test 3: DNS resolution
        try:
            import socket
            import time
            start_time = time.time()
            socket.gethostbyname("google.com")
            dns_time = time.time() - start_time
            test_results.append({
                "test": "DNS resolution",
                "status": "✅ PASSED",
                "endpoint": "google.com",
                "response_time": f"{dns_time:.2f}s"
            })
        except Exception as e:
            test_results.append({
                "test": "DNS resolution",
                "status": "❌ FAILED",
                "endpoint": "google.com",
                "error": str(e)
            })
        
        # Determine overall status
        passed_tests = sum(1 for result in test_results if result["status"] == "✅ PASSED")
        total_tests = len([r for r in test_results if r["status"] != "⚠️ SKIPPED"])
        
        overall_status = "healthy" if passed_tests == total_tests else "degraded" if passed_tests > 0 else "unhealthy"
        
        # Update startup status
        startup_status["internet_connectivity"] = (passed_tests == total_tests)
        
        return {
            "ok": True,
            "overall_status": overall_status,
            "summary": f"{passed_tests}/{total_tests} tests passed",
            "test_results": test_results,
            "startup_status_updated": startup_status["internet_connectivity"]
        }
        
    except Exception as e:
        error_msg = f"Internet connectivity check error: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return {"ok": False, "message": "Error during connectivity check", "error": str(e)}
    
    
# Include routers
app.include_router(profile_router)
app.include_router(auth_router)
app.include_router(kundli_router)
app.include_router(kundli_generate_router)
app.include_router(payments_router)