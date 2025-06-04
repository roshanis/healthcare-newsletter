# Email Troubleshooting Guide

## Quick Email Test

First, run the email diagnostic tool:

```bash
python email_test.py
```

This will test your configuration, SMTP connection, and send a test email.

## Common Email Issues & Solutions

### 🔐 Gmail Authentication Error

**Problem**: `SMTPAuthenticationError: Username and Password not accepted`

**Solution**: You need an App Password, not your regular Gmail password.

1. **Enable 2-Factor Authentication**:
   - Go to https://myaccount.google.com/security
   - Enable 2-Step Verification

2. **Generate App Password**:
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" as the app
   - Copy the 16-character password (format: xxxx xxxx xxxx xxxx)

3. **Update .env file**:
   ```bash
   EMAIL_FROM=your_email@gmail.com
   EMAIL_PASSWORD=your_16_char_app_password  # Not your regular password!
   EMAIL_TO=recipient@example.com
   ```

### 📧 Email Not Received

**Check these locations**:
1. **Spam/Junk folder** - Most common issue
2. **Promotions tab** (Gmail)
3. **Quarantine** (corporate email)
4. **Blocked senders** list

**Troubleshooting steps**:
```bash
# Test with a simple email first
python email_test.py

# Check logs for delivery confirmation
tail -f logs/newsletter_security.log
```

### 🔒 Outlook/Hotmail Setup

**SMTP Settings**:
```bash
EMAIL_SMTP_SERVER=smtp-mail.outlook.com
EMAIL_SMTP_PORT=587
EMAIL_FROM=your_email@outlook.com
EMAIL_PASSWORD=your_password  # Regular password works
```

**Note**: Outlook may require "Less secure app access" to be enabled.

### 🏢 Corporate Email Issues

**Common problems**:
- Firewall blocking SMTP ports
- Proxy server interference
- Corporate security policies

**Solutions**:
1. **Check with IT department** about SMTP access
2. **Try different ports**: 587, 465, 25
3. **Use webmail instead** of SMTP if available
4. **VPN might help** if on corporate network

### 📨 Yahoo Mail Setup

**SMTP Settings**:
```bash
EMAIL_SMTP_SERVER=smtp.mail.yahoo.com
EMAIL_SMTP_PORT=587
EMAIL_FROM=your_email@yahoo.com
EMAIL_PASSWORD=your_app_password  # Yahoo also requires app passwords
```

### 🔧 Other Email Providers

**Common SMTP settings**:

| Provider | SMTP Server | Port | Auth Required |
|----------|-------------|------|---------------|
| Gmail | smtp.gmail.com | 587 | App Password |
| Outlook | smtp-mail.outlook.com | 587 | Password |
| Yahoo | smtp.mail.yahoo.com | 587 | App Password |
| Apple iCloud | smtp.mail.me.com | 587 | App Password |
| Comcast | smtp.comcast.net | 587 | Password |

### 🚨 Debugging Steps

1. **Test basic configuration**:
   ```bash
   python email_test.py
   ```

2. **Check environment variables**:
   ```bash
   # Make sure .env file exists and has correct values
   cat .env
   ```

3. **Test SMTP manually**:
   ```python
   import smtplib
   server = smtplib.SMTP('smtp.gmail.com', 587)
   server.starttls()
   server.login('your_email@gmail.com', 'your_app_password')
   print("Success!")
   server.quit()
   ```

4. **Check logs**:
   ```bash
   # Look for detailed error messages
   tail -f logs/newsletter_security.log
   tail -f newsletter_scheduler.log
   ```

## Error Messages & Solutions

### `[Errno 61] Connection refused`
- **Cause**: SMTP server/port wrong or firewall blocking
- **Solution**: Check SMTP settings, try different ports

### `SSL: CERTIFICATE_VERIFY_FAILED`
- **Cause**: SSL certificate issues
- **Solution**: Update certificates or use TLS instead

### `Message rejected: 550 Authentication required`
- **Cause**: SMTP server requires authentication
- **Solution**: Enable authentication, check credentials

### `Too many recipients`
- **Cause**: Sending to too many people at once
- **Solution**: System limits to 50 recipients for security

## Testing Your Fix

After making changes:

1. **Test configuration**:
   ```bash
   python email_test.py
   ```

2. **Test newsletter generation**:
   ```bash
   python scheduler.py --test
   ```

3. **Send real newsletter**:
   ```bash
   python scheduler.py --manual
   ```

## Advanced Debugging

### Enable SMTP Debug Mode

Add this to your test script:
```python
import smtplib
smtplib.SMTP.debuglevel = 1  # Enable debug output
```

### Check Detailed Logs

```bash
# Security events
tail -f logs/security_events.log

# General application logs  
tail -f logs/newsletter_security.log

# Check for authentication failures
grep -i "auth" logs/*.log
```

### Network Connectivity Test

```bash
# Test if SMTP port is reachable
telnet smtp.gmail.com 587

# Or use netcat
nc -zv smtp.gmail.com 587
```

## Still Having Issues?

1. **Run full diagnostics**:
   ```bash
   python email_test.py
   python security_test.py
   ```

2. **Check your email provider's documentation**
3. **Try a different email provider** (Gmail usually works best)
4. **Consider using a dedicated email service** like SendGrid for production

## Security Notes

- **Never commit passwords** to version control
- **Use App Passwords** when available
- **Monitor failed login attempts** in email provider
- **Rotate passwords regularly**
- **Check email quotas** to avoid being blocked

---

**Need more help?** Check the logs in `logs/` directory for detailed error messages.