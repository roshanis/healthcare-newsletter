# Healthcare Newsletter Generator

An automated weekly newsletter system focused on healthcare payer news and innovation projects. Scrapes content from hospitalogy.com and other healthcare websites, filters for relevant content, and generates AI-powered summaries.

## Features

- 🏥 **Healthcare Focus**: Specifically targets payer and innovation content
- 🤖 **AI-Powered Summaries**: Uses OpenAI GPT-4 to generate professional newsletter content
- 📅 **Weekly Automation**: Automated scheduling for consistent delivery
- 🔗 **Extensible Sources**: Easily add new healthcare websites
- 📧 **Email Distribution**: Automatic email delivery to subscribers
- 🎯 **Smart Filtering**: Relevance scoring and categorization
- 🔒 **Security Hardened**: Input validation, rate limiting, secure file operations

## Quick Start

### 1. Installation

```bash
# Clone or create the project directory
cd healthcare-newsletter

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create your environment file:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```bash
# Required: OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# Required: Email Configuration
EMAIL_FROM=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_TO=recipient1@example.com,recipient2@example.com

# Optional: Customize settings
NEWSLETTER_NAME=Healthcare Weekly
ORGANIZATION_NAME=Your Company
```

### 3. Security Validation

```bash
# Run security tests first
python security_test.py

# Test newsletter generation
python scheduler.py --test
```

### 4. Generate Your First Newsletter

```bash
# Manual generation with email
python scheduler.py --manual

# Start automated weekly scheduler
python scheduler.py --schedule
```

## Configuration Options

### Environment Variables (.env)
- **OPENAI_API_KEY**: Your OpenAI API key (required)
- **EMAIL_FROM**: Sender email address
- **EMAIL_PASSWORD**: Email app password (for Gmail)
- **EMAIL_TO**: Comma-separated recipient emails
- **EMAIL_SMTP_SERVER**: SMTP server (default: smtp.gmail.com)
- **EMAIL_SMTP_PORT**: SMTP port (default: 587)
- **NEWSLETTER_NAME**: Custom newsletter title
- **ORGANIZATION_NAME**: Your organization name

### Content Filtering (config.json)
- **Payer Keywords**: Insurance, medicaid, medicare, claims, etc.
- **Innovation Keywords**: AI, digital health, telehealth, blockchain, etc.
- **Relevance Scoring**: Automatic content prioritization

### Scheduling (config.json)
- **Day**: Any day of the week (default: Monday)
- **Time**: 24-hour format (default: 09:00)
- **Timezone**: Configure for your location

## Website Sources

### Currently Supported
- **Hospitalogy.com**: Healthcare strategy and innovation
- **Healthcare IT News**: Technology and digital health
- **Fierce Healthcare**: Payer and innovation news

### Adding New Sources

Create a new scraper in `website_scrapers.py`:

```python
class YourWebsiteScraper(BaseScraper):
    def __init__(self):
        super().__init__("https://yoursite.com", "Your Site Name")
    
    def get_article_links(self) -> List[str]:
        # Implement link extraction
        pass
    
    def scrape_article(self, url: str) -> Optional[Article]:
        # Implement article scraping
        pass
```

Register the scraper in `ScraperManager`:

```python
scraper_manager.add_scraper('yoursite', YourWebsiteScraper())
```

## Usage Examples

### Manual Newsletter Generation

```python
from newsletter_generator import NewsletterGenerator

generator = NewsletterGenerator("config.json")
content = generator.create_newsletter()
generator.save_newsletter(content)
print(content)
```

### Scheduled Automation

```bash
# Start scheduler (runs in background)
python scheduler.py --schedule

# Check next run time
python scheduler.py --next
```

### Testing and Development

```bash
# Test without sending emails
python scheduler.py --test

# Generate sample content
python newsletter_generator.py
```

## Output Formats

### Newsletter Structure
- **Executive Summary**: Key insights in 2-3 sentences
- **Payer News**: Insurance and payment-related articles
- **Innovation & Technology**: Digital health and tech developments
- **Notable Trends**: AI-generated trend analysis

### File Outputs
- **Markdown Files**: Saved in `newsletters/` directory
- **Statistics**: Generation metrics in JSON format
- **Logs**: Detailed operation logs

## Customization

### Content Focus
Modify keywords in `config.json`:

```json
{
  "keywords": {
    "payer_keywords": ["value-based care", "risk adjustment"],
    "innovation_keywords": ["interoperability", "API integration"]
  }
}
```

### AI Prompts
Edit prompts in `newsletter_generator.py`:

```python
prompt = f"""
Create a newsletter focused on your specific interests...
"""
```

### Email Templates
Customize email formatting in the `send_email` method.

## Monitoring and Maintenance

### Logs
- **Application Logs**: `newsletter_scheduler.log`
- **Error Notifications**: Automatic email alerts
- **Statistics**: Weekly generation metrics

### Error Handling
- **Website Unavailable**: Graceful degradation
- **API Failures**: Fallback content generation
- **Email Failures**: Logged for manual retry

## Security Features

### 🔒 Built-in Security Controls
- **Input Validation**: All URLs, emails, and filenames validated
- **HTML Sanitization**: XSS protection for all content
- **Rate Limiting**: 50 requests/hour per operation to prevent abuse
- **File Security**: Path traversal protection, size limits
- **Network Security**: HTTPS enforcement, SSL verification
- **Email Security**: SMTP TLS, recipient limits, content sanitization

### 🛡️ Security Testing
```bash
# Run comprehensive security tests
python security_test.py

# Check security logs
tail -f logs/security_events.log
```

### 🔑 Environment Variables Security
- **Never commit .env files** to version control
- Use `.env.example` as a template
- Store all secrets in environment variables
- Rotate API keys and passwords regularly
- Monitor for credential leaks

### 📧 Email Security
- Use app passwords, not account passwords
- Consider OAuth for enhanced security
- Limit SMTP access by IP if possible
- Maximum 50 recipients to prevent spam abuse

## Development

### Project Structure
```
healthcare-newsletter/
├── newsletter_generator.py    # Main newsletter logic
├── website_scrapers.py       # Extensible web scrapers
├── scheduler.py              # Automation and scheduling
├── config.json              # Configuration template
├── requirements.txt         # Python dependencies
├── newsletters/             # Generated newsletters
└── README.md               # This file
```

### Contributing
1. Add new website scrapers
2. Improve content filtering algorithms
3. Enhance email templates
4. Add new output formats

## Troubleshooting

### Common Issues

**OpenAI API Errors**
- Check API key validity
- Verify account credits
- Monitor rate limits

**Email Delivery**
- Test SMTP settings manually
- Check spam folders
- Verify app password setup

**Website Scraping**
- Monitor for site structure changes
- Check robots.txt compliance
- Handle rate limiting

### Support
- Review logs in `newsletter_scheduler.log`
- Test individual components
- Check configuration file syntax

## License

This project is open source. Please respect website terms of service when scraping content.

## Future Enhancements

- [ ] Web dashboard for management
- [ ] RSS feed integration
- [ ] Social media sharing
- [ ] PDF newsletter generation
- [ ] Analytics and engagement tracking
- [ ] Multi-language support