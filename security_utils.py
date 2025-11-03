#!/usr/bin/env python3
"""
Security utilities for healthcare newsletter system
Provides input validation, sanitization, and security controls
"""

import re
import os
import html
import urllib.parse
from typing import Union, List, Dict, Any
import json
import logging
import requests
from pathlib import Path

logger = logging.getLogger(__name__)

class SecurityError(Exception):
    """Custom exception for security violations"""
    pass

class SecurityValidator:
    """Handles input validation and sanitization"""
    
    # Allowed file extensions for safe file operations
    ALLOWED_EXTENSIONS = {'.json', '.md', '.txt', '.log'}
    
    # Maximum file sizes (in bytes)
    MAX_CONFIG_SIZE = 1024 * 1024  # 1MB
    MAX_CONTENT_SIZE = 10 * 1024 * 1024  # 10MB
    
    # Safe filename pattern (alphanumeric, hyphens, underscores, dots)
    SAFE_FILENAME_PATTERN = re.compile(r'^[a-zA-Z0-9_.-]+$')
    
    # URL validation pattern
    SAFE_URL_PATTERN = re.compile(
        r'^https?://'  # http or https
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    # Known scraper keys that do not require URL validation
    KNOWN_WEBSITE_KEYS = {"hospitalogy", "healthcareitnews", "fiercehealthcare"}
    
    @staticmethod
    def validate_url(url: str) -> str:
        """Validate and sanitize URL"""
        if not isinstance(url, str):
            raise SecurityError("URL must be a string")
        
        url = url.strip()
        if len(url) > 2000:  # Reasonable URL length limit
            raise SecurityError("URL too long")
        
        if not SecurityValidator.SAFE_URL_PATTERN.match(url):
            raise SecurityError(f"Invalid URL format: {url}")
        
        # Only allow HTTPS for external sites (except localhost for development)
        if not url.startswith('https://') and not url.startswith('http://localhost'):
            raise SecurityError("Only HTTPS URLs are allowed for external sites")
        
        return url
    
    @staticmethod
    def validate_filename(filename: str, base_dir: str = None) -> str:
        """Validate filename for safe file operations"""
        if not isinstance(filename, str):
            raise SecurityError("Filename must be a string")
        
        filename = filename.strip()
        if not filename:
            raise SecurityError("Filename cannot be empty")
        
        if len(filename) > 255:  # Standard filesystem limit
            raise SecurityError("Filename too long")
        
        # Check for path traversal attempts
        if '..' in filename or '/' in filename or '\\' in filename:
            raise SecurityError("Path traversal detected in filename")
        
        # Check filename pattern
        if not SecurityValidator.SAFE_FILENAME_PATTERN.match(filename):
            raise SecurityError(f"Invalid filename format: {filename}")
        
        # Check file extension
        ext = Path(filename).suffix.lower()
        if ext not in SecurityValidator.ALLOWED_EXTENSIONS:
            raise SecurityError(f"File extension not allowed: {ext}")
        
        # If base_dir provided, ensure final path is within it
        if base_dir:
            full_path = Path(base_dir) / filename
            try:
                full_path.resolve().relative_to(Path(base_dir).resolve())
            except ValueError:
                raise SecurityError("Path traversal detected")
        
        return filename
    
    @staticmethod
    def sanitize_html(content: str) -> str:
        """Sanitize HTML content to prevent XSS"""
        if not isinstance(content, str):
            return str(content)
        
        # HTML escape
        return html.escape(content)
    
    @staticmethod
    def sanitize_email(email: str) -> str:
        """Validate and sanitize email address"""
        if not isinstance(email, str):
            raise SecurityError("Email must be a string")
        
        email = email.strip().lower()
        
        # Basic email pattern validation
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if not email_pattern.match(email):
            raise SecurityError(f"Invalid email format: {email}")
        
        if len(email) > 254:  # RFC 5321 limit
            raise SecurityError("Email address too long")
        
        return email
    
    @staticmethod
    def validate_json_config(config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration data structure"""
        if not isinstance(config_data, dict):
            raise SecurityError("Configuration must be a dictionary")
        
        # Define allowed configuration keys
        allowed_keys = {
            'websites', 'keywords', 'scheduling', 'newsletter_settings',
            'payer_keywords', 'innovation_keywords'
        }
        
        # Check for unexpected keys (potential injection)
        for key in config_data.keys():
            if key not in allowed_keys:
                logger.warning(f"Unexpected configuration key: {key}")
        
        # Validate websites array
        if 'websites' in config_data:
            if not isinstance(config_data['websites'], list):
                raise SecurityError("Websites must be a list")
            
            validated_websites = []
            for url in config_data['websites']:
                if isinstance(url, str) and url.strip().lower() in SecurityValidator.KNOWN_WEBSITE_KEYS:
                    validated_websites.append(url.strip())
                else:
                    validated_websites.append(SecurityValidator.validate_url(url))
            config_data['websites'] = validated_websites
        
        return config_data

class SecureFileHandler:
    """Handles file operations with security controls"""
    
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.base_dir = self.base_dir.resolve()
    
    def safe_read_file(self, filename: str, max_size: int = None) -> str:
        """Safely read file with validation"""
        validated_filename = SecurityValidator.validate_filename(filename, str(self.base_dir))
        file_path = self.base_dir / validated_filename
        
        # Check if file exists and is within base directory
        if not file_path.exists():
            raise SecurityError(f"File not found: {filename}")
        
        if not file_path.is_file():
            raise SecurityError(f"Path is not a file: {filename}")
        
        # Check file size
        file_size = file_path.stat().st_size
        max_size = max_size or SecurityValidator.MAX_CONTENT_SIZE
        if file_size > max_size:
            raise SecurityError(f"File too large: {file_size} bytes")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return content
        except UnicodeDecodeError:
            raise SecurityError("File contains invalid UTF-8 characters")
        except PermissionError:
            raise SecurityError("Permission denied reading file")
    
    def safe_write_file(self, filename: str, content: str, max_size: int = None) -> str:
        """Safely write file with validation"""
        validated_filename = SecurityValidator.validate_filename(filename, str(self.base_dir))
        file_path = self.base_dir / validated_filename
        
        # Validate content size
        content_size = len(content.encode('utf-8'))
        max_size = max_size or SecurityValidator.MAX_CONTENT_SIZE
        if content_size > max_size:
            raise SecurityError(f"Content too large: {content_size} bytes")
        
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return str(file_path)
        except PermissionError:
            raise SecurityError("Permission denied writing file")

class SecureHTTPClient:
    """HTTP client with security controls"""
    
    def __init__(self):
        self.session = None
        self.setup_session()
    
    def setup_session(self):
        """Setup secure HTTP session"""
        self.session = requests.Session()
        
        # Security headers
        self.session.headers.update({
            'User-Agent': 'HealthcareNewsletter/1.0 (Security-Hardened)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Set timeouts
        self.session.timeout = (10, 30)  # (connect_timeout, read_timeout)
    
    def safe_get(self, url: str, max_size: int = 5 * 1024 * 1024) -> requests.Response:
        """Safely fetch URL with validation"""
        validated_url = SecurityValidator.validate_url(url)
        
        try:
            response = self.session.get(
                validated_url,
                timeout=(10, 30),
                allow_redirects=True,
                stream=True
            )
            response.raise_for_status()
            
            # Check content length
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > max_size:
                raise SecurityError(f"Response too large: {content_length} bytes")
            
            # Read content with size limit
            content = b''
            for chunk in response.iter_content(chunk_size=8192):
                content += chunk
                if len(content) > max_size:
                    raise SecurityError("Response content too large")
            
            response._content = content
            return response
            
        except requests.exceptions.SSLError:
            raise SecurityError(f"SSL verification failed for {url}")
        except requests.exceptions.ConnectionError:
            raise SecurityError(f"Connection failed to {url}")
        except requests.exceptions.Timeout:
            raise SecurityError(f"Request timeout for {url}")
        except requests.exceptions.RequestException as e:
            raise SecurityError(f"HTTP request failed: {e}")

def secure_json_loads(data: str) -> Dict[str, Any]:
    """Safely parse JSON with security controls"""
    if not isinstance(data, str):
        raise SecurityError("JSON data must be a string")
    
    if len(data) > SecurityValidator.MAX_CONFIG_SIZE:
        raise SecurityError("JSON data too large")
    
    try:
        parsed_data = json.loads(data)
        return SecurityValidator.validate_json_config(parsed_data)
    except json.JSONDecodeError as e:
        raise SecurityError(f"Invalid JSON: {e}")

def setup_secure_logging():
    """Setup secure logging configuration"""
    # Create logs directory securely
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Configure logging with security considerations
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/newsletter_security.log'),
            logging.StreamHandler()
        ]
    )
    
    # Set up security-specific logger
    security_logger = logging.getLogger('security')
    security_handler = logging.FileHandler('logs/security_events.log')
    security_handler.setFormatter(
        logging.Formatter('%(asctime)s - SECURITY - %(levelname)s - %(message)s')
    )
    security_logger.addHandler(security_handler)
    
    return security_logger

# Rate limiting for protection against abuse
class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self, max_requests: int = 100, time_window: int = 3600):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = {}
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed for identifier"""
        import time
        
        current_time = time.time()
        
        # Clean old entries
        self.requests = {
            k: v for k, v in self.requests.items() 
            if current_time - v['first_request'] < self.time_window
        }
        
        if identifier not in self.requests:
            self.requests[identifier] = {
                'count': 1,
                'first_request': current_time
            }
            return True
        
        request_data = self.requests[identifier]
        if request_data['count'] >= self.max_requests:
            return False
        
        request_data['count'] += 1
        return True
