#!/usr/bin/env python3
"""
Healthcare Newsletter Generator
Generates weekly newsletters focused on healthcare payer news and innovation
from hospitalogy.com and other configurable sources.
"""

import requests
from bs4 import BeautifulSoup
import openai
from datetime import datetime, timedelta
import json
import re
import schedule
import time
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from dotenv import load_dotenv
from pathlib import Path
from security_utils import (
    SecurityValidator, SecureFileHandler, SecureHTTPClient, 
    SecurityError, secure_json_loads, setup_secure_logging, RateLimiter
)

# Setup secure logging
security_logger = setup_secure_logging()
logger = logging.getLogger(__name__)

@dataclass
class Article:
    title: str
    url: str
    content: str
    published_date: Optional[str] = None
    relevance_score: float = 0.0
    category: str = ""

class NewsletterGenerator:
    def __init__(self, config_path: str = "config.json"):
        # Load environment variables
        load_dotenv()
        
        # Initialize security components
        self.file_handler = SecureFileHandler()
        self.http_client = SecureHTTPClient()
        self.rate_limiter = RateLimiter(max_requests=50, time_window=3600)  # 50 requests per hour
        
        self.config = self.load_config(config_path)
        
        # Get OpenAI API key from environment with validation
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            security_logger.error("OpenAI API key not found in environment variables")
            raise ValueError("OPENAI_API_KEY not found in environment variables. Please check your .env file.")
        
        if len(openai_api_key) < 20:  # Basic API key length validation
            security_logger.error("OpenAI API key appears to be invalid (too short)")
            raise ValueError("OpenAI API key appears to be invalid")
        
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        
        # Keywords for filtering payer and innovation content
        self.payer_keywords = [
            "payer", "insurance", "medicaid", "medicare", "health plan",
            "coverage", "reimbursement", "payment", "claims", "benefits",
            "premium", "deductible", "copay", "prior authorization"
        ]
        
        self.innovation_keywords = [
            "innovation", "technology", "digital health", "AI", "artificial intelligence",
            "machine learning", "telehealth", "telemedicine", "mobile health", "mHealth",
            "blockchain", "cloud", "analytics", "data", "platform", "startup",
            "venture capital", "funding", "partnership", "collaboration"
        ]
        
    def load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file and environment variables with security validation"""
        try:
            # Validate config file path
            validated_path = SecurityValidator.validate_filename(config_path)
            
            # Default configuration with validated environment variables
            default_config = {
                "websites": ["https://hospitalogy.com/"],
                "email_settings": {
                    "smtp_server": os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com"),
                    "smtp_port": int(os.getenv("EMAIL_SMTP_PORT", "587")),
                    "from_email": "",
                    "password": "",
                    "to_emails": []
                },
                "newsletter_settings": {
                    "name": os.getenv("NEWSLETTER_NAME", "Healthcare Weekly Newsletter"),
                    "organization": os.getenv("ORGANIZATION_NAME", "")
                }
            }
            
            # Validate and set email settings from environment
            email_from = os.getenv("EMAIL_FROM", "")
            if email_from:
                try:
                    default_config["email_settings"]["from_email"] = SecurityValidator.sanitize_email(email_from)
                except SecurityError as e:
                    security_logger.error(f"Invalid email address in EMAIL_FROM: {e}")
                    raise ValueError(f"Invalid email configuration: {e}")
            
            email_password = os.getenv("EMAIL_PASSWORD", "")
            if email_password:
                if len(email_password) < 8:  # Basic password length check
                    security_logger.error("Email password appears too short")
                    raise ValueError("Email password appears to be invalid")
                default_config["email_settings"]["password"] = email_password
            
            email_to = os.getenv("EMAIL_TO", "")
            if email_to:
                to_emails = []
                for email in email_to.split(","):
                    email = email.strip()
                    if email:
                        try:
                            to_emails.append(SecurityValidator.sanitize_email(email))
                        except SecurityError as e:
                            security_logger.error(f"Invalid email address in EMAIL_TO: {email}")
                            raise ValueError(f"Invalid recipient email: {e}")
                default_config["email_settings"]["to_emails"] = to_emails
            
            # Try to load additional config from JSON file
            try:
                file_content = self.file_handler.safe_read_file(validated_path, max_size=64*1024)  # 64KB max
                file_config = secure_json_loads(file_content)
                
                # Merge configurations (file config takes precedence for non-sensitive data)
                for key, value in file_config.items():
                    if key not in ["openai_api_key"] and key != "email_settings":
                        default_config[key] = value
                        
            except SecurityError as e:
                security_logger.error(f"Security error loading config: {e}")
                raise ValueError(f"Configuration security error: {e}")
            except FileNotFoundError:
                logger.info(f"Config file {config_path} not found. Using environment variables and defaults.")
            
            return default_config
            
        except Exception as e:
            security_logger.error(f"Error loading configuration: {e}")
            raise
    
    def scrape_hospitalogy(self) -> List[Article]:
        """Scrape articles from hospitalogy.com with security controls"""
        articles = []
        base_url = "https://hospitalogy.com/"
        
        # Rate limiting check
        if not self.rate_limiter.is_allowed("hospitalogy_scrape"):
            security_logger.warning("Rate limit exceeded for hospitalogy scraping")
            raise SecurityError("Rate limit exceeded. Please wait before trying again.")
        
        try:
            # Use secure HTTP client
            response = self.http_client.safe_get(base_url)
            
            # Parse with security in mind
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for article links with validation
            article_links = soup.find_all('a', href=True)
            
            processed_count = 0
            for link in article_links:
                if processed_count >= 20:  # Hard limit
                    break
                    
                href = link.get('href')
                if href and ('article' in href.lower() or 'news' in href.lower()):
                    try:
                        # Construct and validate URL
                        if not href.startswith('http'):
                            href = f"https://hospitalogy.com{href}"
                        
                        validated_url = SecurityValidator.validate_url(href)
                        
                        title = link.get_text(strip=True)
                        title = SecurityValidator.sanitize_html(title)
                        
                        if title and len(title) > 10 and len(title) < 500:  # Reasonable title length
                            article = self.scrape_article_content(validated_url, title)
                            if article:
                                articles.append(article)
                                processed_count += 1
                                
                    except SecurityError as e:
                        security_logger.warning(f"Security error processing link {href}: {e}")
                        continue
                    except Exception as e:
                        logger.warning(f"Error processing link {href}: {e}")
                        continue
                            
        except SecurityError as e:
            security_logger.error(f"Security error scraping hospitalogy.com: {e}")
            raise
        except Exception as e:
            logger.error(f"Error scraping hospitalogy.com: {e}")
            
        return articles
    
    def scrape_article_content(self, url: str, title: str) -> Optional[Article]:
        """Scrape content from individual article with security validation"""
        try:
            # Validate inputs
            validated_url = SecurityValidator.validate_url(url)
            sanitized_title = SecurityValidator.sanitize_html(title)
            
            # Rate limiting for individual articles
            if not self.rate_limiter.is_allowed(f"article_{validated_url}"):
                security_logger.warning(f"Rate limit exceeded for article: {validated_url}")
                return None
            
            # Use secure HTTP client
            response = self.http_client.safe_get(validated_url, max_size=2*1024*1024)  # 2MB max
            
            # Parse with security controls
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove potentially dangerous elements
            for tag in soup(['script', 'style', 'iframe', 'object', 'embed', 'form']):
                tag.decompose()
            
            # Extract main content (adjust selectors based on site structure)
            content_selectors = ['article', '.content', '.post-content', '.entry-content', 'main']
            content = ""
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content = content_elem.get_text(separator=' ', strip=True)
                    break
            
            if not content:
                # Fallback: get all paragraph text
                paragraphs = soup.find_all('p')
                content = ' '.join([p.get_text(strip=True) for p in paragraphs])
            
            # Sanitize and limit content
            content = SecurityValidator.sanitize_html(content)
            content = content[:3000]  # Reasonable content length limit
            
            if len(content) < 50:  # Skip articles with too little content
                return None
            
            return Article(title=sanitized_title, url=validated_url, content=content)
            
        except SecurityError as e:
            security_logger.warning(f"Security error scraping article {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error scraping article {url}: {e}")
            return None
    
    def calculate_relevance_score(self, article: Article) -> float:
        """Calculate relevance score based on payer and innovation keywords"""
        text = f"{article.title} {article.content}".lower()
        
        payer_matches = sum(1 for keyword in self.payer_keywords if keyword in text)
        innovation_matches = sum(1 for keyword in self.innovation_keywords if keyword in text)
        
        # Weighted scoring
        payer_score = payer_matches * 2  # Higher weight for payer content
        innovation_score = innovation_matches * 1.5
        
        total_words = len(text.split())
        if total_words == 0:
            return 0.0
        
        # Normalize by content length
        score = (payer_score + innovation_score) / (total_words / 100)
        return min(score, 10.0)  # Cap at 10
    
    def categorize_article(self, article: Article) -> str:
        """Categorize article based on content"""
        text = f"{article.title} {article.content}".lower()
        
        payer_matches = sum(1 for keyword in self.payer_keywords if keyword in text)
        innovation_matches = sum(1 for keyword in self.innovation_keywords if keyword in text)
        
        if payer_matches > innovation_matches:
            return "Payer News"
        elif innovation_matches > payer_matches:
            return "Innovation & Technology"
        else:
            return "General Healthcare"
    
    def filter_articles(self, articles: List[Article], min_score: float = 1.0) -> List[Article]:
        """Filter and score articles based on relevance"""
        filtered_articles = []
        
        for article in articles:
            score = self.calculate_relevance_score(article)
            category = self.categorize_article(article)
            
            article.relevance_score = score
            article.category = category
            
            if score >= min_score:
                filtered_articles.append(article)
        
        # Sort by relevance score
        return sorted(filtered_articles, key=lambda x: x.relevance_score, reverse=True)
    
    def generate_summary(self, articles: List[Article]) -> str:
        """Generate AI-powered newsletter summary"""
        if not articles:
            return "No relevant articles found this week."
        
        # Prepare content for AI summarization
        content = "\n\n".join([
            f"Title: {article.title}\nCategory: {article.category}\nContent: {article.content[:500]}..."
            for article in articles[:10]  # Limit to top 10 articles
        ])
        
        prompt = f"""
        Create a professional weekly healthcare newsletter summary focused on payer news and healthcare innovation.
        
        Based on the following articles, create:
        1. An executive summary (2-3 sentences)
        2. Key highlights organized by category (Payer News, Innovation & Technology)
        3. Notable trends or insights
        
        Articles:
        {content}
        
        Format the response as a professional newsletter with clear sections and bullet points.
        Focus on actionable insights for healthcare executives and payer organizations.
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating AI summary: {e}")
            return self.generate_fallback_summary(articles)
    
    def generate_fallback_summary(self, articles: List[Article]) -> str:
        """Generate basic summary without AI"""
        summary = "# Healthcare Weekly: Payer & Innovation Report\n\n"
        summary += f"**Week of {datetime.now().strftime('%B %d, %Y')}**\n\n"
        
        # Group by category
        categories = {}
        for article in articles[:15]:
            if article.category not in categories:
                categories[article.category] = []
            categories[article.category].append(article)
        
        for category, cat_articles in categories.items():
            summary += f"## {category}\n\n"
            for article in cat_articles[:5]:
                summary += f"- **{article.title}**\n"
                summary += f"  {article.content[:200]}...\n"
                summary += f"  [Read more]({article.url})\n\n"
        
        return summary
    
    def create_newsletter(self) -> str:
        """Create complete newsletter"""
        logger.info("Starting newsletter generation...")
        
        # Collect articles from all sources
        all_articles = []
        
        # Scrape hospitalogy.com
        hospitalogy_articles = self.scrape_hospitalogy()
        all_articles.extend(hospitalogy_articles)
        
        # Filter and rank articles
        relevant_articles = self.filter_articles(all_articles)
        
        logger.info(f"Found {len(relevant_articles)} relevant articles")
        
        # Generate newsletter content
        newsletter_content = self.generate_summary(relevant_articles)
        
        # Add metadata
        newsletter_name = self.config.get("newsletter_settings", {}).get("name", "Healthcare Weekly Newsletter")
        organization = self.config.get("newsletter_settings", {}).get("organization", "")
        org_line = f"**{organization}**\n" if organization else ""
        
        header = f"""
# {newsletter_name}
{org_line}**Generated on {datetime.now().strftime('%A, %B %d, %Y')}**
**Focus: Payer News & Healthcare Innovation**

---

"""
        
        footer = f"""

---

*This newsletter was automatically generated from healthcare industry sources.*
*Generated {len(relevant_articles)} articles from {len(all_articles)} total articles.*

**Next newsletter:** {(datetime.now() + timedelta(days=7)).strftime('%B %d, %Y')}
"""
        
        return header + newsletter_content + footer
    
    def save_newsletter(self, content: str, filename: str = None) -> str:
        """Save newsletter to file with security validation"""
        try:
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d')
                filename = f"healthcare_newsletter_{timestamp}.md"
            
            # Validate filename
            validated_filename = SecurityValidator.validate_filename(filename)
            
            # Sanitize content
            sanitized_content = SecurityValidator.sanitize_html(content)
            
            # Use secure file handler
            newsletters_dir = Path("newsletters")
            newsletters_dir.mkdir(exist_ok=True)
            
            file_handler = SecureFileHandler(str(newsletters_dir))
            filepath = file_handler.safe_write_file(validated_filename, sanitized_content)
            
            logger.info(f"Newsletter saved to {filepath}")
            return filepath
            
        except SecurityError as e:
            security_logger.error(f"Security error saving newsletter: {e}")
            raise ValueError(f"Failed to save newsletter: {e}")
        except Exception as e:
            logger.error(f"Error saving newsletter: {e}")
            raise
    
    def send_email(self, content: str, subject: str = None):
        """Send newsletter via email with security validation"""
        try:
            if not subject:
                subject = f"Healthcare Weekly Newsletter - {datetime.now().strftime('%B %d, %Y')}"
            
            # Sanitize inputs
            sanitized_content = SecurityValidator.sanitize_html(content)
            sanitized_subject = SecurityValidator.sanitize_html(subject)
            
            # Validate subject length
            if len(sanitized_subject) > 200:
                sanitized_subject = sanitized_subject[:200] + "..."
            
            email_config = self.config.get("email_settings", {})
            
            if not email_config.get("from_email") or not email_config.get("to_emails"):
                logger.warning("Email configuration incomplete. Skipping email send.")
                return
            
            # Rate limiting for email sending
            if not self.rate_limiter.is_allowed("email_send"):
                security_logger.warning("Rate limit exceeded for email sending")
                raise SecurityError("Email rate limit exceeded")
            
            # Validate email configuration
            from_email = email_config["from_email"]
            to_emails = email_config["to_emails"]
            
            # Limit number of recipients to prevent abuse
            if len(to_emails) > 50:
                security_logger.error(f"Too many email recipients: {len(to_emails)}")
                raise SecurityError("Too many email recipients")
            
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = ", ".join(to_emails)
            msg['Subject'] = sanitized_subject
            
            # Convert markdown to HTML with security controls
            html_content = sanitized_content.replace('\n', '<br>')
            html_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html_content)
            html_content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html_content)
            html_content = re.sub(r'# (.*?)$', r'<h1>\1</h1>', html_content, flags=re.MULTILINE)
            html_content = re.sub(r'## (.*?)$', r'<h2>\1</h2>', html_content, flags=re.MULTILINE)
            
            # Additional security: Remove any remaining HTML that could be dangerous
            html_content = re.sub(r'<script.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            html_content = re.sub(r'<iframe.*?</iframe>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            
            msg.attach(MIMEText(html_content, 'html'))
            
            # Secure SMTP connection with detailed logging
            logger.info(f"Connecting to SMTP server: {email_config['smtp_server']}:{email_config['smtp_port']}")
            server = smtplib.SMTP(email_config["smtp_server"], email_config["smtp_port"])
            
            logger.info("Starting TLS encryption...")
            server.starttls()  # Enable TLS encryption
            
            logger.info(f"Authenticating as: {email_config['from_email']}")
            server.login(email_config["from_email"], email_config["password"])
            
            logger.info(f"Sending email to {len(to_emails)} recipients...")
            server.send_message(msg)
            server.quit()
            
            logger.info(f"✅ Newsletter sent successfully to {len(to_emails)} recipients: {', '.join(to_emails)}")
            security_logger.info(f"Email sent successfully to {len(to_emails)} recipients")
            
        except SecurityError as e:
            security_logger.error(f"Security error sending email: {e}")
            raise
        except smtplib.SMTPAuthenticationError as e:
            security_logger.error(f"SMTP authentication failed: {e}")
            logger.error("❌ Email authentication failed!")
            logger.error("🔧 Troubleshooting steps:")
            logger.error("1. For Gmail: Use an App Password, not your regular password")
            logger.error("2. Enable 2-factor authentication first")
            logger.error("3. Generate App Password: https://myaccount.google.com/apppasswords")
            logger.error("4. Run: python email_test.py to debug")
            raise ValueError("Email authentication failed - check credentials and use App Password for Gmail")
        except smtplib.SMTPException as e:
            security_logger.error(f"SMTP error: {e}")
            logger.error(f"❌ SMTP server error: {e}")
            logger.error("🔧 Check your SMTP server settings in .env file")
            raise ValueError(f"Email sending failed: {e}")
        except Exception as e:
            security_logger.error(f"Unexpected error sending email: {e}")
            logger.error(f"❌ Unexpected email error: {e}")
            logger.error("🔧 Run: python email_test.py for detailed debugging")
            raise
    
    def run_weekly_generation(self):
        """Generate and distribute weekly newsletter"""
        try:
            content = self.create_newsletter()
            filepath = self.save_newsletter(content)
            self.send_email(content)
            logger.info("Weekly newsletter generation completed successfully")
        except SecurityError as e:
            security_logger.error(f"Security error in weekly newsletter generation: {e}")
            logger.error("Weekly newsletter generation failed due to security violation")
        except Exception as e:
            # Don't expose internal details in logs that might be user-visible
            security_logger.error(f"Unexpected error in weekly newsletter generation: {e}")
            logger.error("Weekly newsletter generation failed due to system error")

def main():
    """Main function to run newsletter generator"""
    generator = NewsletterGenerator()
    
    # Generate newsletter immediately
    content = generator.create_newsletter()
    filepath = generator.save_newsletter(content)
    
    print(f"Newsletter generated and saved to: {filepath}")
    print("\nNewsletter preview:")
    print("=" * 50)
    print(content[:1000] + "..." if len(content) > 1000 else content)
    print("=" * 50)
    
    # Schedule weekly generation (uncomment to enable scheduling)
    # schedule.every().monday.at("09:00").do(generator.run_weekly_generation)
    # 
    # print("Newsletter scheduled to run every Monday at 9:00 AM")
    # while True:
    #     schedule.run_pending()
    #     time.sleep(3600)  # Check every hour

if __name__ == "__main__":
    main()