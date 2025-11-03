"""
Extensible website scrapers for healthcare newsletter generation
Easily add new healthcare websites for content scraping
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
import re
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

@dataclass
class Article:
    title: str
    url: str
    content: str
    published_date: Optional[str] = None
    relevance_score: float = 0.0
    category: str = ""
    source_website: str = ""

class BaseScraper(ABC):
    """Base class for website scrapers"""
    
    def __init__(self, base_url: str, name: str):
        self.base_url = base_url
        self.name = name
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    @abstractmethod
    def get_article_links(self) -> List[str]:
        """Get list of article URLs from the website"""
        pass
    
    @abstractmethod
    def scrape_article(self, url: str) -> Optional[Article]:
        """Scrape individual article content"""
        pass
    
    def scrape_all_articles(self, limit: int = 20) -> List[Article]:
        """Scrape all articles from the website"""
        articles = []
        try:
            links = self.get_article_links()
            for url in links[:limit]:
                article = self.scrape_article(url)
                if article:
                    article.source_website = self.name
                    articles.append(article)
        except Exception as e:
            logger.error(f"Error scraping {self.name}: {e}")
        
        return articles

class HospitalogyScraper(BaseScraper):
    """Scraper for hospitalogy.com"""
    
    def __init__(self):
        super().__init__("https://hospitalogy.com", "Hospitalogy")
    
    def get_article_links(self) -> List[str]:
        """Get article links from hospitalogy.com"""
        links = []
        try:
            response = self.session.get(self.base_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for article links - adjust selectors based on actual site structure
            article_selectors = [
                'a[href*="/article"]',
                'a[href*="/news"]',
                'a[href*="/post"]',
                '.article-title a',
                '.post-title a',
                'h2 a',
                'h3 a'
            ]
            
            for selector in article_selectors:
                elements = soup.select(selector)
                for element in elements:
                    href = element.get('href')
                    if href:
                        full_url = urljoin(self.base_url, href)
                        if self._is_valid_article_url(full_url):
                            links.append(full_url)
            
            # Remove duplicates while preserving order
            links = list(dict.fromkeys(links))
            
        except Exception as e:
            logger.error(f"Error getting article links from {self.name}: {e}")
        
        return links
    
    def _is_valid_article_url(self, url: str) -> bool:
        """Check if URL is a valid article URL"""
        parsed = urlparse(url)
        if parsed.netloc != urlparse(self.base_url).netloc:
            return False
        
        # Skip non-article URLs
        skip_patterns = [
            '/category/', '/tag/', '/author/', '/page/',
            '/contact', '/about', '/privacy', '/terms',
            '.pdf', '.jpg', '.png', '.gif'
        ]
        
        return not any(pattern in url.lower() for pattern in skip_patterns)
    
    def scrape_article(self, url: str) -> Optional[Article]:
        """Scrape individual article from hospitalogy.com"""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title_selectors = ['h1', '.article-title', '.post-title', '.entry-title', 'title']
            title = ""
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    break
            
            # Extract content
            content_selectors = [
                '.article-content', '.post-content', '.entry-content',
                'article', '.content', 'main'
            ]
            
            content = ""
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # Remove script and style elements
                    for elem in content_elem(['script', 'style', 'nav', 'header', 'footer']):
                        elem.decompose()
                    content = content_elem.get_text(separator=' ', strip=True)
                    break
            
            # Fallback: get all paragraph text
            if not content:
                paragraphs = soup.find_all('p')
                content = ' '.join([p.get_text(strip=True) for p in paragraphs])
            
            # Extract date if available
            date_selectors = ['.date', '.published', '.post-date', 'time', '[datetime]']
            published_date = None
            for selector in date_selectors:
                date_elem = soup.select_one(selector)
                if date_elem:
                    published_date = date_elem.get('datetime') or date_elem.get_text(strip=True)
                    break
            
            if title and content:
                return Article(
                    title=title,
                    url=url,
                    content=content[:3000],  # Limit content length
                    published_date=published_date
                )
            
        except Exception as e:
            logger.error(f"Error scraping article {url}: {e}")
        
        return None

class HealthcareITNewsScraper(BaseScraper):
    """Scraper for healthcareitnews.com"""
    
    def __init__(self):
        super().__init__("https://www.healthcareitnews.com", "Healthcare IT News")
    
    def get_article_links(self) -> List[str]:
        """Get article links from healthcareitnews.com"""
        links = []
        try:
            response = self.session.get(self.base_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for article links
            article_links = soup.find_all('a', href=True)
            
            for link in article_links:
                href = link.get('href')
                if href and ('/news/' in href or '/article/' in href):
                    full_url = urljoin(self.base_url, href)
                    if self._is_valid_article_url(full_url):
                        links.append(full_url)
            
            links = list(dict.fromkeys(links))
            
        except Exception as e:
            logger.error(f"Error getting article links from {self.name}: {e}")
        
        return links
    
    def _is_valid_article_url(self, url: str) -> bool:
        """Check if URL is a valid article URL"""
        return '/news/' in url or '/article/' in url
    
    def scrape_article(self, url: str) -> Optional[Article]:
        """Scrape individual article"""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title_elem = soup.find('h1') or soup.find('title')
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # Extract content
            content_elem = soup.find('article') or soup.find('.content')
            if content_elem:
                for elem in content_elem(['script', 'style', 'nav', 'header', 'footer']):
                    elem.decompose()
                content = content_elem.get_text(separator=' ', strip=True)
            else:
                paragraphs = soup.find_all('p')
                content = ' '.join([p.get_text(strip=True) for p in paragraphs])
            
            if title and content:
                return Article(
                    title=title,
                    url=url,
                    content=content[:3000]
                )
            
        except Exception as e:
            logger.error(f"Error scraping article {url}: {e}")
        
        return None

class FierceHealthcareScraper(BaseScraper):
    """Scraper for fiercehealthcare.com"""
    
    def __init__(self):
        super().__init__("https://www.fiercehealthcare.com", "Fierce Healthcare")
    
    def get_article_links(self) -> List[str]:
        """Get article links from fiercehealthcare.com"""
        links = []
        try:
            response = self.session.get(self.base_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            article_links = soup.find_all('a', href=True)
            
            for link in article_links:
                href = link.get('href')
                if href and ('/payer/' in href or '/tech/' in href or '/innovation/' in href):
                    full_url = urljoin(self.base_url, href)
                    links.append(full_url)
            
            links = list(dict.fromkeys(links))
            
        except Exception as e:
            logger.error(f"Error getting article links from {self.name}: {e}")
        
        return links
    
    def _is_valid_article_url(self, url: str) -> bool:
        """Check if URL is a valid article URL"""
        return any(path in url for path in ['/payer/', '/tech/', '/innovation/'])
    
    def scrape_article(self, url: str) -> Optional[Article]:
        """Scrape individual article"""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            title_elem = soup.find('h1')
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            content_elem = soup.find('article') or soup.find('.article-body')
            if content_elem:
                for elem in content_elem(['script', 'style', 'nav', 'header', 'footer']):
                    elem.decompose()
                content = content_elem.get_text(separator=' ', strip=True)
            else:
                paragraphs = soup.find_all('p')
                content = ' '.join([p.get_text(strip=True) for p in paragraphs])
            
            if title and content:
                return Article(
                    title=title,
                    url=url,
                    content=content[:3000]
                )
            
        except Exception as e:
            logger.error(f"Error scraping article {url}: {e}")
        
        return None

class STATNewsScraper(BaseScraper):
    """Scraper for statnews.com"""
    
    def __init__(self):
        super().__init__("https://www.statnews.com", "STAT News")
    
    def get_article_links(self) -> List[str]:
        """Get article links from statnews.com"""
        links = []
        try:
            response = self.session.get(self.base_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            article_links = soup.find_all('a', href=True)
            
            for link in article_links:
                href = link.get('href')
                if href and ('statnews.com' in href or href.startswith('/')):
                    full_url = urljoin(self.base_url, href)
                    if self._is_valid_article_url(full_url):
                        links.append(full_url)
            
            links = list(dict.fromkeys(links))
            
        except Exception as e:
            logger.error(f"Error getting article links from {self.name}: {e}")
        
        return links
    
    def _is_valid_article_url(self, url: str) -> bool:
        """Check if URL is a valid article URL"""
        parsed = urlparse(url)
        if 'statnews.com' not in parsed.netloc:
            return False
        
        skip_patterns = [
            '/category/', '/tag/', '/author/', '/page/',
            '/contact', '/about', '/privacy', '/terms',
            '.pdf', '.jpg', '.png', '.gif', '/subscribe'
        ]
        
        return not any(pattern in url.lower() for pattern in skip_patterns)
    
    def scrape_article(self, url: str) -> Optional[Article]:
        """Scrape individual article"""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            title_elem = soup.find('h1')
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            content_elem = soup.find('article') or soup.find('.article-content')
            if content_elem:
                for elem in content_elem(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                    elem.decompose()
                content = content_elem.get_text(separator=' ', strip=True)
            else:
                paragraphs = soup.find_all('p')
                content = ' '.join([p.get_text(strip=True) for p in paragraphs])
            
            if title and content:
                return Article(
                    title=title,
                    url=url,
                    content=content[:3000]
                )
            
        except Exception as e:
            logger.error(f"Error scraping article {url}: {e}")
        
        return None

class KFFHealthNewsScraper(BaseScraper):
    """Scraper for kffhealthnews.org (Kaiser Health News)"""
    
    def __init__(self):
        super().__init__("https://kffhealthnews.org", "Kaiser Health News")
    
    def get_article_links(self) -> List[str]:
        """Get article links from kffhealthnews.org"""
        links = []
        try:
            response = self.session.get(self.base_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            article_links = soup.find_all('a', href=True)
            
            for link in article_links:
                href = link.get('href')
                if href:
                    full_url = urljoin(self.base_url, href)
                    if self._is_valid_article_url(full_url):
                        links.append(full_url)
            
            links = list(dict.fromkeys(links))
            
        except Exception as e:
            logger.error(f"Error getting article links from {self.name}: {e}")
        
        return links
    
    def _is_valid_article_url(self, url: str) -> bool:
        """Check if URL is a valid article URL"""
        parsed = urlparse(url)
        if 'kffhealthnews.org' not in parsed.netloc:
            return False
        
        skip_patterns = [
            '/category/', '/tag/', '/author/', '/page/',
            '/contact', '/about', '/privacy', '/terms',
            '.pdf', '.jpg', '.png', '.gif', '/newsletter'
        ]
        
        return not any(pattern in url.lower() for pattern in skip_patterns) and len(parsed.path) > 1
    
    def scrape_article(self, url: str) -> Optional[Article]:
        """Scrape individual article"""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            title_elem = soup.find('h1')
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            content_elem = soup.find('article') or soup.find('.entry-content')
            if content_elem:
                for elem in content_elem(['script', 'style', 'nav', 'header', 'footer']):
                    elem.decompose()
                content = content_elem.get_text(separator=' ', strip=True)
            else:
                paragraphs = soup.find_all('p')
                content = ' '.join([p.get_text(strip=True) for p in paragraphs])
            
            if title and content:
                return Article(
                    title=title,
                    url=url,
                    content=content[:3000]
                )
            
        except Exception as e:
            logger.error(f"Error scraping article {url}: {e}")
        
        return None

class HealthcareDiveScraper(BaseScraper):
    """Scraper for healthcaredive.com"""
    
    def __init__(self):
        super().__init__("https://www.healthcaredive.com", "Healthcare Dive")
    
    def get_article_links(self) -> List[str]:
        """Get article links from healthcaredive.com"""
        links = []
        try:
            response = self.session.get(self.base_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            article_links = soup.find_all('a', href=True)
            
            for link in article_links:
                href = link.get('href')
                if href and '/news/' in href:
                    full_url = urljoin(self.base_url, href)
                    links.append(full_url)
            
            links = list(dict.fromkeys(links))
            
        except Exception as e:
            logger.error(f"Error getting article links from {self.name}: {e}")
        
        return links
    
    def _is_valid_article_url(self, url: str) -> bool:
        """Check if URL is a valid article URL"""
        return '/news/' in url
    
    def scrape_article(self, url: str) -> Optional[Article]:
        """Scrape individual article"""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            title_elem = soup.find('h1')
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            content_elem = soup.find('article') or soup.find('.article-body')
            if content_elem:
                for elem in content_elem(['script', 'style', 'nav', 'header', 'footer']):
                    elem.decompose()
                content = content_elem.get_text(separator=' ', strip=True)
            else:
                paragraphs = soup.find_all('p')
                content = ' '.join([p.get_text(strip=True) for p in paragraphs])
            
            if title and content:
                return Article(
                    title=title,
                    url=url,
                    content=content[:3000]
                )
            
        except Exception as e:
            logger.error(f"Error scraping article {url}: {e}")
        
        return None

class MobiHealthNewsScraper(BaseScraper):
    """Scraper for mobihealthnews.com"""
    
    def __init__(self):
        super().__init__("https://www.mobihealthnews.com", "Mobi Health News")
    
    def get_article_links(self) -> List[str]:
        """Get article links from mobihealthnews.com"""
        links = []
        try:
            response = self.session.get(self.base_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            article_links = soup.find_all('a', href=True)
            
            for link in article_links:
                href = link.get('href')
                if href:
                    full_url = urljoin(self.base_url, href)
                    if self._is_valid_article_url(full_url):
                        links.append(full_url)
            
            links = list(dict.fromkeys(links))
            
        except Exception as e:
            logger.error(f"Error getting article links from {self.name}: {e}")
        
        return links
    
    def _is_valid_article_url(self, url: str) -> bool:
        """Check if URL is a valid article URL"""
        parsed = urlparse(url)
        if 'mobihealthnews.com' not in parsed.netloc:
            return False
        
        skip_patterns = [
            '/category/', '/tag/', '/author/', '/page/',
            '/contact', '/about', '/privacy', '/terms',
            '.pdf', '.jpg', '.png', '.gif'
        ]
        
        return not any(pattern in url.lower() for pattern in skip_patterns) and len(parsed.path) > 1
    
    def scrape_article(self, url: str) -> Optional[Article]:
        """Scrape individual article"""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            title_elem = soup.find('h1')
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            content_elem = soup.find('article')
            if content_elem:
                for elem in content_elem(['script', 'style', 'nav', 'header', 'footer']):
                    elem.decompose()
                content = content_elem.get_text(separator=' ', strip=True)
            else:
                paragraphs = soup.find_all('p')
                content = ' '.join([p.get_text(strip=True) for p in paragraphs])
            
            if title and content:
                return Article(
                    title=title,
                    url=url,
                    content=content[:3000]
                )
            
        except Exception as e:
            logger.error(f"Error scraping article {url}: {e}")
        
        return None

class FierceBiotechScraper(BaseScraper):
    """Scraper for fiercebiotech.com"""
    
    def __init__(self):
        super().__init__("https://www.fiercebiotech.com", "Fierce Biotech")
    
    def get_article_links(self) -> List[str]:
        """Get article links from fiercebiotech.com"""
        links = []
        try:
            response = self.session.get(self.base_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            article_links = soup.find_all('a', href=True)
            
            for link in article_links:
                href = link.get('href')
                if href:
                    full_url = urljoin(self.base_url, href)
                    if 'fiercebiotech.com' in full_url and len(urlparse(full_url).path) > 1:
                        links.append(full_url)
            
            links = list(dict.fromkeys(links))
            
        except Exception as e:
            logger.error(f"Error getting article links from {self.name}: {e}")
        
        return links
    
    def scrape_article(self, url: str) -> Optional[Article]:
        """Scrape individual article"""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            title_elem = soup.find('h1')
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            content_elem = soup.find('article') or soup.find('.article-body')
            if content_elem:
                for elem in content_elem(['script', 'style', 'nav', 'header', 'footer']):
                    elem.decompose()
                content = content_elem.get_text(separator=' ', strip=True)
            else:
                paragraphs = soup.find_all('p')
                content = ' '.join([p.get_text(strip=True) for p in paragraphs])
            
            if title and content:
                return Article(
                    title=title,
                    url=url,
                    content=content[:3000]
                )
            
        except Exception as e:
            logger.error(f"Error scraping article {url}: {e}")
        
        return None

class BeckersHospitalReviewScraper(BaseScraper):
    """Scraper for beckershospitalreview.com"""
    
    def __init__(self):
        super().__init__("https://www.beckershospitalreview.com", "Becker's Hospital Review")
    
    def get_article_links(self) -> List[str]:
        """Get article links from beckershospitalreview.com"""
        links = []
        try:
            response = self.session.get(self.base_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            article_links = soup.find_all('a', href=True)
            
            for link in article_links:
                href = link.get('href')
                if href:
                    full_url = urljoin(self.base_url, href)
                    if self._is_valid_article_url(full_url):
                        links.append(full_url)
            
            links = list(dict.fromkeys(links))
            
        except Exception as e:
            logger.error(f"Error getting article links from {self.name}: {e}")
        
        return links
    
    def _is_valid_article_url(self, url: str) -> bool:
        """Check if URL is a valid article URL"""
        parsed = urlparse(url)
        if 'beckershospitalreview.com' not in parsed.netloc:
            return False
        
        skip_patterns = [
            '/category/', '/tag/', '/author/', '/page/',
            '/contact', '/about', '/privacy', '/terms',
            '.pdf', '.jpg', '.png', '.gif'
        ]
        
        return not any(pattern in url.lower() for pattern in skip_patterns) and len(parsed.path) > 1
    
    def scrape_article(self, url: str) -> Optional[Article]:
        """Scrape individual article"""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            title_elem = soup.find('h1')
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            content_elem = soup.find('article') or soup.find('.article-content')
            if content_elem:
                for elem in content_elem(['script', 'style', 'nav', 'header', 'footer']):
                    elem.decompose()
                content = content_elem.get_text(separator=' ', strip=True)
            else:
                paragraphs = soup.find_all('p')
                content = ' '.join([p.get_text(strip=True) for p in paragraphs])
            
            if title and content:
                return Article(
                    title=title,
                    url=url,
                    content=content[:3000]
                )
            
        except Exception as e:
            logger.error(f"Error scraping article {url}: {e}")
        
        return None

class MedPageTodayScraper(BaseScraper):
    """Scraper for medpagetoday.com"""
    
    def __init__(self):
        super().__init__("https://www.medpagetoday.com", "MedPage Today")
    
    def get_article_links(self) -> List[str]:
        """Get article links from medpagetoday.com"""
        links = []
        try:
            response = self.session.get(self.base_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            article_links = soup.find_all('a', href=True)
            
            for link in article_links:
                href = link.get('href')
                if href:
                    full_url = urljoin(self.base_url, href)
                    if self._is_valid_article_url(full_url):
                        links.append(full_url)
            
            links = list(dict.fromkeys(links))
            
        except Exception as e:
            logger.error(f"Error getting article links from {self.name}: {e}")
        
        return links
    
    def _is_valid_article_url(self, url: str) -> bool:
        """Check if URL is a valid article URL"""
        parsed = urlparse(url)
        if 'medpagetoday.com' not in parsed.netloc:
            return False
        
        skip_patterns = [
            '/category/', '/tag/', '/author/', '/page/',
            '/contact', '/about', '/privacy', '/terms',
            '.pdf', '.jpg', '.png', '.gif', '/subscribe'
        ]
        
        return not any(pattern in url.lower() for pattern in skip_patterns) and len(parsed.path) > 1
    
    def scrape_article(self, url: str) -> Optional[Article]:
        """Scrape individual article"""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            title_elem = soup.find('h1')
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            content_elem = soup.find('article')
            if content_elem:
                for elem in content_elem(['script', 'style', 'nav', 'header', 'footer']):
                    elem.decompose()
                content = content_elem.get_text(separator=' ', strip=True)
            else:
                paragraphs = soup.find_all('p')
                content = ' '.join([p.get_text(strip=True) for p in paragraphs])
            
            if title and content:
                return Article(
                    title=title,
                    url=url,
                    content=content[:3000]
                )
            
        except Exception as e:
            logger.error(f"Error scraping article {url}: {e}")
        
        return None

class EndpointsNewsScraper(BaseScraper):
    """Scraper for endpoints.news"""
    
    def __init__(self):
        super().__init__("https://endpoints.news", "Endpoints News")
    
    def get_article_links(self) -> List[str]:
        """Get article links from endpoints.news"""
        links = []
        try:
            response = self.session.get(self.base_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            article_links = soup.find_all('a', href=True)
            
            for link in article_links:
                href = link.get('href')
                if href:
                    full_url = urljoin(self.base_url, href)
                    if self._is_valid_article_url(full_url):
                        links.append(full_url)
            
            links = list(dict.fromkeys(links))
            
        except Exception as e:
            logger.error(f"Error getting article links from {self.name}: {e}")
        
        return links
    
    def _is_valid_article_url(self, url: str) -> bool:
        """Check if URL is a valid article URL"""
        parsed = urlparse(url)
        if 'endpoints.news' not in parsed.netloc:
            return False
        
        skip_patterns = [
            '/category/', '/tag/', '/author/', '/page/',
            '/contact', '/about', '/privacy', '/terms',
            '.pdf', '.jpg', '.png', '.gif', '/subscribe'
        ]
        
        return not any(pattern in url.lower() for pattern in skip_patterns) and len(parsed.path) > 1
    
    def scrape_article(self, url: str) -> Optional[Article]:
        """Scrape individual article"""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            title_elem = soup.find('h1')
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            content_elem = soup.find('article')
            if content_elem:
                for elem in content_elem(['script', 'style', 'nav', 'header', 'footer']):
                    elem.decompose()
                content = content_elem.get_text(separator=' ', strip=True)
            else:
                paragraphs = soup.find_all('p')
                content = ' '.join([p.get_text(strip=True) for p in paragraphs])
            
            if title and content:
                return Article(
                    title=title,
                    url=url,
                    content=content[:3000]
                )
            
        except Exception as e:
            logger.error(f"Error scraping article {url}: {e}")
        
        return None

class ScraperManager:
    """Manages multiple website scrapers"""
    
    def __init__(self):
        self.scrapers = {
            'hospitalogy': HospitalogyScraper(),
            'healthcareitnews': HealthcareITNewsScraper(),
            'fiercehealthcare': FierceHealthcareScraper(),
            'statnews': STATNewsScraper(),
            'kffhealthnews': KFFHealthNewsScraper(),
            'healthcaredive': HealthcareDiveScraper(),
            'mobihealthnews': MobiHealthNewsScraper(),
            'fiercebiotech': FierceBiotechScraper(),
            'beckershospitalreview': BeckersHospitalReviewScraper(),
            'medpagetoday': MedPageTodayScraper(),
            'endpointsnews': EndpointsNewsScraper()
        }
    
    def add_scraper(self, name: str, scraper: BaseScraper):
        """Add a new scraper"""
        self.scrapers[name] = scraper
    
    def scrape_website(self, website_name: str, limit: int = 20) -> List[Article]:
        """Scrape articles from a specific website"""
        if website_name not in self.scrapers:
            logger.error(f"Unknown website: {website_name}")
            return []
        
        return self.scrapers[website_name].scrape_all_articles(limit)
    
    def scrape_all_websites(self, limit_per_site: int = 20) -> List[Article]:
        """Scrape articles from all configured websites"""
        all_articles = []
        
        for name, scraper in self.scrapers.items():
            logger.info(f"Scraping {name}...")
            articles = scraper.scrape_all_articles(limit_per_site)
            all_articles.extend(articles)
            logger.info(f"Found {len(articles)} articles from {name}")
        
        return all_articles
    
    def get_available_websites(self) -> List[str]:
        """Get list of available website scrapers"""
        return list(self.scrapers.keys())

# Example of how to add a new website scraper
class NewWebsiteScraper(BaseScraper):
    """Template for adding new website scrapers"""
    
    def __init__(self):
        super().__init__("https://example.com", "Example Site")
    
    def get_article_links(self) -> List[str]:
        # Implement link extraction logic
        return []
    
    def scrape_article(self, url: str) -> Optional[Article]:
        # Implement article scraping logic
        return None