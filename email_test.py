#!/usr/bin/env python3
"""
Email Testing and Debugging Script
Tests email configuration and delivery
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_email_config():
    """Test email configuration from environment variables"""
    load_dotenv()
    
    # Get email settings
    email_from = os.getenv("EMAIL_FROM")
    email_password = os.getenv("EMAIL_PASSWORD")
    email_to = os.getenv("EMAIL_TO")
    smtp_server = os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("EMAIL_SMTP_PORT", "587"))
    
    print("🔍 Email Configuration Check:")
    print("=" * 40)
    print(f"From Email: {email_from}")
    print(f"To Email(s): {email_to}")
    print(f"SMTP Server: {smtp_server}")
    print(f"SMTP Port: {smtp_port}")
    print(f"Password Set: {'✅' if email_password else '❌'}")
    print()
    
    # Validate required settings
    if not email_from:
        print("❌ ERROR: EMAIL_FROM not set in .env file")
        return False
    
    if not email_password:
        print("❌ ERROR: EMAIL_PASSWORD not set in .env file")
        return False
    
    if not email_to:
        print("❌ ERROR: EMAIL_TO not set in .env file")
        return False
    
    # Check email format
    if "@" not in email_from:
        print("❌ ERROR: EMAIL_FROM is not a valid email address")
        return False
    
    # Check recipient emails
    to_emails = [email.strip() for email in email_to.split(",")]
    for email in to_emails:
        if "@" not in email:
            print(f"❌ ERROR: Invalid recipient email: {email}")
            return False
    
    print("✅ Configuration looks good!")
    return True

def test_smtp_connection():
    """Test SMTP server connection"""
    load_dotenv()
    
    email_from = os.getenv("EMAIL_FROM")
    email_password = os.getenv("EMAIL_PASSWORD")
    smtp_server = os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("EMAIL_SMTP_PORT", "587"))
    
    print("🔌 Testing SMTP Connection:")
    print("=" * 40)
    
    try:
        print(f"Connecting to {smtp_server}:{smtp_port}...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        print("✅ Connection established")
        
        print("Starting TLS...")
        server.starttls()
        print("✅ TLS started")
        
        print("Attempting login...")
        server.login(email_from, email_password)
        print("✅ Login successful")
        
        server.quit()
        print("✅ SMTP test completed successfully!")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Check your email and password are correct")
        print("2. For Gmail, use an App Password (not your regular password)")
        print("3. Enable 2-factor authentication and generate an App Password")
        print("4. Go to: https://myaccount.google.com/apppasswords")
        return False
        
    except smtplib.SMTPException as e:
        print(f"❌ SMTP error: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Check your internet connection")
        print("2. Verify SMTP server and port are correct")
        print("3. Check if firewall is blocking the connection")
        return False

def send_test_email():
    """Send a test email"""
    load_dotenv()
    
    email_from = os.getenv("EMAIL_FROM")
    email_password = os.getenv("EMAIL_PASSWORD")
    email_to = os.getenv("EMAIL_TO")
    smtp_server = os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("EMAIL_SMTP_PORT", "587"))
    
    to_emails = [email.strip() for email in email_to.split(",")]
    
    print("📧 Sending Test Email:")
    print("=" * 40)
    
    try:
        # Create test message
        msg = MIMEMultipart()
        msg['From'] = email_from
        msg['To'] = ", ".join(to_emails)
        msg['Subject'] = "Healthcare Newsletter - Email Test"
        
        body = """
        <h2>Email Test Successful! 🎉</h2>
        <p>This is a test email from your Healthcare Newsletter system.</p>
        <p><strong>Configuration Status:</strong> ✅ Working correctly</p>
        <p><strong>Next Steps:</strong></p>
        <ul>
            <li>Your email setup is working</li>
            <li>You can now generate newsletters</li>
            <li>Run: <code>python scheduler.py --test</code></li>
        </ul>
        <hr>
        <p><em>Healthcare Newsletter System - Email Test</em></p>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(email_from, email_password)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Test email sent successfully to {len(to_emails)} recipient(s)")
        print(f"📫 Check these inboxes: {', '.join(to_emails)}")
        print("\n📝 If you don't see the email:")
        print("1. Check spam/junk folder")
        print("2. Wait a few minutes for delivery")
        print("3. Verify recipient email addresses are correct")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send test email: {e}")
        return False

def gmail_setup_guide():
    """Print Gmail setup instructions"""
    print("📧 Gmail Setup Guide:")
    print("=" * 40)
    print("For Gmail accounts, you need an App Password:")
    print()
    print("1. Enable 2-Factor Authentication:")
    print("   https://myaccount.google.com/security")
    print()
    print("2. Generate App Password:")
    print("   https://myaccount.google.com/apppasswords")
    print("   - Select 'Mail' as the app")
    print("   - Copy the 16-character password")
    print()
    print("3. Update your .env file:")
    print("   EMAIL_FROM=your_email@gmail.com")
    print("   EMAIL_PASSWORD=your_16_char_app_password")
    print("   EMAIL_TO=recipient@example.com")
    print()
    print("4. Common SMTP settings:")
    print("   Gmail: smtp.gmail.com:587")
    print("   Outlook: smtp-mail.outlook.com:587")
    print("   Yahoo: smtp.mail.yahoo.com:587")

def main():
    """Main testing function"""
    print("🔧 Healthcare Newsletter - Email Debugging Tool")
    print("=" * 50)
    
    # Test 1: Configuration
    if not test_email_config():
        print("\n❌ Email configuration issues found!")
        gmail_setup_guide()
        return
    
    print()
    
    # Test 2: SMTP Connection
    if not test_smtp_connection():
        print("\n❌ SMTP connection failed!")
        gmail_setup_guide()
        return
    
    print()
    
    # Test 3: Send test email
    if send_test_email():
        print("\n🎉 All email tests passed! Your configuration is working.")
        print("\nNext steps:")
        print("1. Run: python scheduler.py --test")
        print("2. Check the generated newsletter")
        print("3. Run: python scheduler.py --manual (to send newsletter)")
    else:
        print("\n❌ Email sending failed!")
        gmail_setup_guide()

if __name__ == "__main__":
    main()