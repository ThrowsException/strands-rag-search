import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from urllib.parse import urlparse
import re

from ..items import PageItem


class MySpider(CrawlSpider):
    name = "ibx"
    allowed_domains = ["ibx.com"]
    start_urls = ["https://www.ibx.com/resources/for-members"]
    
    # Configure crawling rules
    rules = (
        # Follow all internal links and parse them
        Rule(
            LinkExtractor(
                allow_domains=["ibx.com"],
                deny_extensions=['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 
                               'zip', 'rar', '7z', 'tar', 'gz', 'exe', 'dmg', 'pkg',
                               'mp3', 'mp4', 'avi', 'mov', 'wmv', 'flv', 'webm',
                               'jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'ico',
                               'css', 'js', 'xml', 'rss', 'atom'],
                canonicalize=True,
                unique=True
            ),
            callback='parse_page',
            follow=True
        ),
    )

    def parse_page(self, response):
        """Parse each page and extract content"""
        self.logger.info(f"Parsing page: {response.url}")
        
        # Create PageItem with extracted data
        item = PageItem()
        item['url'] = response.url
        item['title'] = self.extract_title(response)
        item['content'] = self.extract_content(response)
        item['links'] = self.extract_links(response)
        item['status_code'] = response.status
        item['meta_description'] = self.extract_meta_description(response)
        item['meta_keywords'] = self.extract_meta_keywords(response)
        item['headings'] = self.extract_headings(response)
        item['html_content'] = response.text  # Store raw HTML
        
        yield item

    def extract_title(self, response):
        """Extract page title"""
        title = response.css('title::text').get()
        if title:
            return title.strip()
        
        # Fallback to h1
        h1 = response.css('h1::text').get()
        if h1:
            return h1.strip()
        
        return "No Title"

    def extract_content(self, response):
        """Extract clean text content from page"""
        # Remove script and style elements
        text_parts = []
        
        # Get text from common content areas
        for selector in ['main', 'article', '.content', '#content', '.post', '.entry']:
            content = response.css(f'{selector}').get()
            if content:
                # Remove HTML tags and get text
                text = scrapy.Selector(text=content).css('*::text').getall()
                text_parts.extend([t.strip() for t in text if t.strip()])
                break
        
        # If no specific content area found, get all body text
        if not text_parts:
            text_parts = response.css('body *::text').getall()
            text_parts = [t.strip() for t in text_parts if t.strip()]
        
        # Clean and join text
        content = ' '.join(text_parts)
        
        # Remove extra whitespace
        content = re.sub(r'\s+', ' ', content)
        
        return content.strip()

    def extract_links(self, response):
        """Extract all links from the page"""
        links = response.css('a::attr(href)').getall()
        absolute_links = []
        
        for link in links:
            absolute_link = response.urljoin(link)
            if validators.url(absolute_link):
                absolute_links.append(absolute_link)
        
        return list(set(absolute_links))  # Remove duplicates

    def extract_meta_description(self, response):
        """Extract meta description"""
        return response.css('meta[name="description"]::attr(content)').get() or ""

    def extract_meta_keywords(self, response):
        """Extract meta keywords"""
        return response.css('meta[name="keywords"]::attr(content)').get() or ""

    def extract_headings(self, response):
        """Extract all headings (h1-h6)"""
        headings = {}
        for i in range(1, 7):  # h1 to h6
            headings[f'h{i}'] = response.css(f'h{i}::text').getall()
        return headings

