"""
Middleware components for the FastAPI application.
"""

import time

from utils.logger import get_logger

logger = get_logger()


class AccessLogMiddleware:
    """Enhanced middleware to log HTTP access requests using our custom logger.
    
    Handles:
    - HTTP/1.0, HTTP/1.1, HTTP/2.0, HTTP/3.0
    - IPv4 and IPv6 addresses
    - Forwarded headers (for proxy scenarios)
    - WebSocket upgrade requests
    - Various scope types
    
    Ensures consistent log format with zero placeholders for unknown values.
    """
    
    def __init__(self, app):
        self.app = app
    
    def _get_client_ip(self, scope):
        """Extract client IP considering forwarded headers and different address formats."""
        # Check for forwarded headers first (common with proxies/load balancers)
        headers = dict(scope.get("headers", []))
        
        # Common forwarded IP headers
        forwarded_headers = [
            b"x-forwarded-for",
            b"x-real-ip", 
            b"x-client-ip",
            b"cf-connecting-ip",  # Cloudflare
        ]
        
        for header_name in forwarded_headers:
            if header_name in headers:
                ip = headers[header_name].decode().split(',')[0].strip()
                if ip and ip != 'unknown':
                    return ip
        
        # Fall back to direct client connection
        client = scope.get("client")
        if client:
            # Handle both IPv4 and IPv6 addresses
            if len(client) >= 1:
                return client[0]
        
        return "unknown"
    
    def _get_http_version(self, scope):
        """Extract HTTP version with fallbacks."""
        # Try to get from scope
        version = scope.get("http_version")
        if version:
            return version
        
        # Check for HTTP/2 (ASGI spec)
        if "h2" in scope.get("extensions", {}):
            return "2.0"
        
        # Check for HTTP/3 (though ASGI doesn't fully support it yet)
        # This is more future-proofing
        if "h3" in scope.get("extensions", {}):
            return "3.0"
        
        # Check headers for HTTP version hints
        headers = dict(scope.get("headers", []))
        if b"http2-settings" in headers:
            return "2.0"
        
        # Default fallback
        return "1.1"
    
    def _get_request_size(self, scope):
        """Get request size if available."""
        headers = dict(scope.get("headers", []))
        content_length = headers.get(b"content-length")
        if content_length:
            try:
                return int(content_length)
            except ValueError:
                pass
        return 0
    
    def _get_response_size(self, message):
        """Get response size if available."""
        if "content-length" in message.get("headers", []):
            try:
                return int(message["headers"][b"content-length"])
            except (ValueError, KeyError):
                pass
        return 0
    
    async def __call__(self, scope, receive, send):
        # Handle different scope types
        if scope["type"] == "http":
            start_time = time.time()
            request_size = self._get_request_size(scope)
            
            # Create a custom send function to capture the response
            async def custom_send(message):
                if message["type"] == "http.response.start":
                    # Log access information when response starts
                    process_time = time.time() - start_time
                    client_ip = self._get_client_ip(scope)
                    method = scope.get("method", "UNKNOWN")
                    path = scope.get("path", "/")
                    http_version = self._get_http_version(scope)
                    status_code = message.get("status", 0)
                    response_size = self._get_response_size(message)
                    
                    # Always log with consistent format: IP - "METHOD PATH HTTP/VERSION" STATUS - REQUEST_SIZE - RESPONSE_SIZE - TIME
                    # Use 0 for unknown/not applicable values to maintain consistent formatting
                    log_message = (
                        f'{client_ip} - "{method} {path} HTTP/{http_version}" '
                        f'{status_code} - {request_size} - {response_size} - {process_time:.3f}s'
                    )
                    
                    access_logger = logger.bind(
                        request_id="-",
                        source_name="fastapi.access",
                        source_function="__call__",
                        source_line=0,
                        access_log=True
                    )
                    
                    access_logger.info(log_message)
                
                await send(message)
            
            await self.app(scope, receive, custom_send)
            
        elif scope["type"] == "websocket":
            # Handle WebSocket upgrade requests
            client_ip = self._get_client_ip(scope)
            path = scope.get("path", "/")
            
            access_logger = logger.bind(
                request_id="-",
                source_name="fastapi.access",
                source_function="__call__",
                source_line=0,
                access_log=True
            )
            
            # Consistent format for WebSocket: IP - "WS PATH" STATUS - 0 - 0 - TIME
            access_logger.info(f'{client_ip} - "WS {path}" 101 - 0 - 0 - 0.000s')
            await self.app(scope, receive, send)
            
        else:
            # Handle other scope types (lifespan, etc.)
            await self.app(scope, receive, send)
