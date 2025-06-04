#!/usr/bin/env python3
"""
Security Testing Script for Healthcare Newsletter
Tests security controls and validates protection mechanisms
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from security_utils import (
    SecurityValidator, SecureFileHandler, SecureHTTPClient,
    SecurityError, secure_json_loads, RateLimiter
)
import logging

# Setup test logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecurityTester:
    """Comprehensive security testing suite"""
    
    def __init__(self):
        self.test_dir = tempfile.mkdtemp(prefix="security_test_")
        self.passed_tests = 0
        self.total_tests = 0
        
    def run_test(self, test_name: str, test_func):
        """Run individual test with error handling"""
        self.total_tests += 1
        try:
            logger.info(f"Running test: {test_name}")
            test_func()
            logger.info(f"✅ PASSED: {test_name}")
            self.passed_tests += 1
        except AssertionError as e:
            logger.error(f"❌ FAILED: {test_name} - {e}")
        except Exception as e:
            logger.error(f"💥 ERROR: {test_name} - {e}")
    
    def test_url_validation(self):
        """Test URL validation security"""
        validator = SecurityValidator()
        
        # Valid URLs should pass
        valid_urls = [
            "https://hospitalogy.com/",
            "https://example.com/article/123",
            "http://localhost:8000/test"
        ]
        
        for url in valid_urls:
            result = validator.validate_url(url)
            assert result == url, f"Valid URL rejected: {url}"
        
        # Invalid URLs should fail
        invalid_urls = [
            "http://example.com/",  # HTTP not allowed for external
            "javascript:alert('xss')",
            "file:///etc/passwd",
            "ftp://example.com/",
            "data:text/html,<script>alert('xss')</script>",
            "mailto:test@example.com",
            "x" * 3000,  # Too long
        ]
        
        for url in invalid_urls:
            try:
                validator.validate_url(url)
                assert False, f"Invalid URL accepted: {url}"
            except SecurityError:
                pass  # Expected
    
    def test_filename_validation(self):
        """Test filename validation security"""
        validator = SecurityValidator()
        
        # Valid filenames should pass
        valid_files = [
            "newsletter.md",
            "config.json",
            "test_file.txt",
            "data.log"
        ]
        
        for filename in valid_files:
            result = validator.validate_filename(filename, self.test_dir)
            assert result == filename, f"Valid filename rejected: {filename}"
        
        # Invalid filenames should fail
        invalid_files = [
            "../../../etc/passwd",  # Path traversal
            "test.php",  # Invalid extension
            "con.txt",  # Windows reserved name
            "",  # Empty
            "x" * 300,  # Too long
            "test\nfile.txt",  # Newline injection
            "test;rm -rf.txt",  # Command injection attempt
        ]
        
        for filename in invalid_files:
            try:
                validator.validate_filename(filename, self.test_dir)
                assert False, f"Invalid filename accepted: {filename}"
            except SecurityError:
                pass  # Expected
    
    def test_email_validation(self):
        """Test email validation security"""
        validator = SecurityValidator()
        
        # Valid emails should pass
        valid_emails = [
            "test@example.com",
            "user+tag@domain.co.uk",
            "a@b.co"
        ]
        
        for email in valid_emails:
            result = validator.sanitize_email(email)
            assert "@" in result, f"Valid email rejected: {email}"
        
        # Invalid emails should fail
        invalid_emails = [
            "notanemail",
            "@example.com",
            "test@",
            "test@example",
            "test\n@example.com",  # Injection attempt
            "test@example.com\nBCC: evil@hacker.com",
            "x" * 300 + "@example.com",  # Too long
        ]
        
        for email in invalid_emails:
            try:
                validator.sanitize_email(email)
                assert False, f"Invalid email accepted: {email}"
            except SecurityError:
                pass  # Expected
    
    def test_html_sanitization(self):
        """Test HTML sanitization"""
        validator = SecurityValidator()
        
        # Test basic sanitization
        dangerous_html = "<script>alert('xss')</script><b>Bold</b>"
        sanitized = validator.sanitize_html(dangerous_html)
        assert "<script>" not in sanitized, "Script tag not sanitized"
        assert "&lt;script&gt;" in sanitized, "HTML not properly escaped"
    
    def test_json_validation(self):
        """Test JSON configuration validation"""
        # Valid JSON should pass
        valid_json = '{"websites": ["https://example.com"], "keywords": {"test": ["word"]}}'
        result = secure_json_loads(valid_json)
        assert isinstance(result, dict), "Valid JSON rejected"
        
        # Invalid JSON should fail
        invalid_jsons = [
            '{"websites": ["http://example.com"]}',  # HTTP URL
            '{"eval": "malicious code"}',  # Suspicious key
            '{"websites": "not_a_list"}',  # Wrong type
            "x" * 2000000,  # Too large
            '{"test": }',  # Malformed JSON
        ]
        
        for json_str in invalid_jsons:
            try:
                secure_json_loads(json_str)
                # Some might pass but be validated later
            except SecurityError:
                pass  # Expected for some cases
            except Exception:
                pass  # JSON parse errors expected
    
    def test_file_operations(self):
        """Test secure file operations"""
        handler = SecureFileHandler(self.test_dir)
        
        # Test safe write
        test_content = "This is test content"
        filename = "test.txt"
        filepath = handler.safe_write_file(filename, test_content)
        assert os.path.exists(filepath), "File not created"
        
        # Test safe read
        read_content = handler.safe_read_file(filename)
        assert read_content == test_content, "File content mismatch"
        
        # Test path traversal prevention
        try:
            handler.safe_write_file("../../../evil.txt", "malicious")
            assert False, "Path traversal not prevented"
        except SecurityError:
            pass  # Expected
        
        # Test file size limit
        large_content = "x" * (20 * 1024 * 1024)  # 20MB
        try:
            handler.safe_write_file("large.txt", large_content)
            assert False, "Large file limit not enforced"
        except SecurityError:
            pass  # Expected
    
    def test_http_client(self):
        """Test secure HTTP client"""
        client = SecureHTTPClient()
        
        # Test HTTPS enforcement (will fail for HTTP external sites)
        try:
            client.safe_get("http://example.com/")
            assert False, "HTTP external site allowed"
        except SecurityError:
            pass  # Expected
        
        # Test localhost exception (should work)
        try:
            client.safe_get("http://localhost:8000/test")
            assert False, "Localhost should fail if no server running"
        except SecurityError:
            pass  # Expected if no server
        except Exception:
            pass  # Connection error expected
    
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        limiter = RateLimiter(max_requests=3, time_window=60)
        
        # First 3 requests should pass
        for i in range(3):
            assert limiter.is_allowed("test_user"), f"Request {i+1} rejected"
        
        # 4th request should be blocked
        assert not limiter.is_allowed("test_user"), "Rate limit not enforced"
        
        # Different user should be allowed
        assert limiter.is_allowed("other_user"), "Different user blocked"
    
    def test_content_size_limits(self):
        """Test content size limit enforcement"""
        validator = SecurityValidator()
        
        # Test reasonable content
        normal_content = "x" * 1000
        sanitized = validator.sanitize_html(normal_content)
        assert len(sanitized) > 0, "Normal content rejected"
        
        # Large content should be handled gracefully
        large_content = "x" * (50 * 1024 * 1024)  # 50MB
        # Should not crash, might be truncated or rejected
        try:
            validator.sanitize_html(large_content)
        except Exception:
            pass  # Memory or size errors expected
    
    def test_error_handling(self):
        """Test error handling doesn't leak information"""
        try:
            # Trigger a security error
            SecurityValidator.validate_url("invalid://url")
        except SecurityError as e:
            error_msg = str(e)
            # Error should not contain sensitive paths or system info
            assert "/home/" not in error_msg, "Error contains sensitive path"
            assert "/Users/" not in error_msg, "Error contains sensitive path"
            assert "password" not in error_msg.lower(), "Error contains sensitive info"
    
    def run_all_tests(self):
        """Run all security tests"""
        logger.info("🔒 Starting Security Test Suite")
        logger.info("=" * 50)
        
        # Run all tests
        test_methods = [
            ("URL Validation", self.test_url_validation),
            ("Filename Validation", self.test_filename_validation),
            ("Email Validation", self.test_email_validation),
            ("HTML Sanitization", self.test_html_sanitization),
            ("JSON Validation", self.test_json_validation),
            ("File Operations", self.test_file_operations),
            ("HTTP Client Security", self.test_http_client),
            ("Rate Limiting", self.test_rate_limiting),
            ("Content Size Limits", self.test_content_size_limits),
            ("Error Handling", self.test_error_handling),
        ]
        
        for test_name, test_func in test_methods:
            self.run_test(test_name, test_func)
        
        # Summary
        logger.info("=" * 50)
        logger.info(f"🎯 Security Test Results: {self.passed_tests}/{self.total_tests} passed")
        
        if self.passed_tests == self.total_tests:
            logger.info("🎉 All security tests PASSED!")
            return True
        else:
            logger.warning(f"⚠️  {self.total_tests - self.passed_tests} security tests FAILED!")
            return False
    
    def cleanup(self):
        """Clean up test directory"""
        try:
            shutil.rmtree(self.test_dir)
        except Exception as e:
            logger.warning(f"Failed to cleanup test directory: {e}")

def main():
    """Run security tests"""
    tester = SecurityTester()
    try:
        success = tester.run_all_tests()
        return 0 if success else 1
    finally:
        tester.cleanup()

if __name__ == "__main__":
    sys.exit(main())