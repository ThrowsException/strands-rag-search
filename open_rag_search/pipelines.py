import json
import csv
import os
import re
from datetime import datetime
from urllib.parse import urlparse
from pathlib import Path
from itemadapter import ItemAdapter


class ProcessPagePipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Add timestamp
        adapter['timestamp'] = datetime.now().isoformat()
        
        # Extract domain
        adapter['domain'] = urlparse(adapter['url']).netloc
        
        # Clean content
        if adapter.get('content'):
            content = adapter['content']
            # Limit content length for storage efficiency
            if len(content) > 10000:
                adapter['content'] = content[:10000] + "..."
        
        return item


class JsonPipeline:
    def __init__(self, output_file='crawl_results.json'):
        self.output_file = output_file
        self.items = []

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            output_file=crawler.settings.get("JSON_OUTPUT_FILE", "crawl_results.json")
        )

    def open_spider(self, spider):
        self.items = []

    def close_spider(self, spider):
        # Write all items to JSON file
        with open(self.output_file, 'w', encoding='utf-8') as f:
            data = {
                "crawl_metadata": {
                    "spider_name": spider.name,
                    "timestamp": datetime.now().isoformat(),
                    "total_pages": len(self.items),
                    "start_urls": spider.start_urls,
                    "allowed_domains": spider.allowed_domains,
                    "max_depth": getattr(spider, 'max_depth', None),
                    "max_pages": getattr(spider, 'max_pages', None)
                },
                "results": self.items
            }
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        spider.logger.info(f"Saved {len(self.items)} items to {self.output_file}")

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        self.items.append(dict(adapter))
        return item


class CsvPipeline:
    def __init__(self, output_file='crawl_results.csv'):
        self.output_file = output_file
        self.file = None
        self.writer = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            output_file=crawler.settings.get("CSV_OUTPUT_FILE", "crawl_results.csv")
        )

    def open_spider(self, spider):
        self.file = open(self.output_file, 'w', newline='', encoding='utf-8')
        self.writer = csv.writer(self.file)
        
        # Write header
        self.writer.writerow([
            'url', 'title', 'content_preview', 'num_links', 'status_code', 
            'depth', 'meta_description', 'meta_keywords', 'domain', 'timestamp'
        ])

    def close_spider(self, spider):
        if self.file:
            self.file.close()
            spider.logger.info(f"Saved results to {self.output_file}")

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Create content preview
        content = adapter.get('content', '')
        content_preview = content[:200] + "..." if len(content) > 200 else content
        
        self.writer.writerow([
            adapter.get('url', ''),
            adapter.get('title', ''),
            content_preview,
            len(adapter.get('links', [])),
            adapter.get('status_code', ''),
            adapter.get('depth', ''),
            adapter.get('meta_description', ''),
            adapter.get('meta_keywords', ''),
            adapter.get('domain', ''),
            adapter.get('timestamp', '')
        ])
        
        return item


class DuplicatesPipeline:
    def __init__(self):
        self.ids_seen = set()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        url = adapter['url']
        
        if url in self.ids_seen:
            spider.logger.info(f"Duplicate item found: {url}")
            return None
        else:
            self.ids_seen.add(url)
            return item


class StatsPipeline:
    def __init__(self):
        self.stats = {
            'total_pages': 0,
            'successful_pages': 0,
            'failed_pages': 0,
            'domains': {},
            'depth_distribution': {},
            'total_content_length': 0
        }

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        self.stats['total_pages'] += 1
        
        if adapter.get('status_code') == 200:
            self.stats['successful_pages'] += 1
        else:
            self.stats['failed_pages'] += 1
        
        # Domain stats
        domain = adapter.get('domain', 'unknown')
        self.stats['domains'][domain] = self.stats['domains'].get(domain, 0) + 1
        
        # Depth stats
        depth = adapter.get('depth', 0)
        self.stats['depth_distribution'][depth] = self.stats['depth_distribution'].get(depth, 0) + 1
        
        # Content length
        content_length = len(adapter.get('content', ''))
        self.stats['total_content_length'] += content_length
        
        return item

    def close_spider(self, spider):
        spider.logger.info("Crawl Statistics:")
        spider.logger.info(f"  Total pages: {self.stats['total_pages']}")
        spider.logger.info(f"  Successful: {self.stats['successful_pages']}")
        spider.logger.info(f"  Failed: {self.stats['failed_pages']}")
        spider.logger.info(f"  Domains crawled: {len(self.stats['domains'])}")
        spider.logger.info(f"  Total content: {self.stats['total_content_length']:,} characters")
        
        if self.stats['total_pages'] > 0:
            avg_content = self.stats['total_content_length'] / self.stats['total_pages']
            spider.logger.info(f"  Average content length: {avg_content:.0f} characters")
        
        # Save stats to file
        with open('crawl_stats.json', 'w') as f:
            json.dump(self.stats, f, indent=2)


class HtmlDownloadPipeline:
    """Pipeline to download and save HTML content to files"""
    
    def __init__(self, download_folder='html_downloads'):
        self.download_folder = download_folder
        self.url_mapping = {}
        self.file_counter = {}  # Track filename conflicts
        
    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            download_folder=crawler.settings.get("HTML_DOWNLOAD_FOLDER", "html_downloads")
        )
    
    def open_spider(self, spider):
        """Create download directory structure"""
        self.base_path = Path(self.download_folder)
        self.base_path.mkdir(exist_ok=True)
        
        # Create domain-specific folder
        domain_folder = self.base_path / spider.allowed_domains[0] if spider.allowed_domains else self.base_path / "unknown"
        domain_folder.mkdir(exist_ok=True)
        self.domain_path = domain_folder
        
        spider.logger.info(f"HTML files will be saved to: {self.domain_path}")
    
    def close_spider(self, spider):
        """Save URL mapping index"""
        index_file = self.base_path / "url_mapping.json"
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(self.url_mapping, f, indent=2, ensure_ascii=False)
        
        spider.logger.info(f"Saved {len(self.url_mapping)} HTML files")
        spider.logger.info(f"URL mapping saved to: {index_file}")
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Skip if no HTML content
        html_content = adapter.get('html_content')
        if not html_content:
            return item
        
        url = adapter.get('url', '')
        
        # Generate safe filename from URL
        filename = self.generate_filename(url)
        
        # Handle filename conflicts
        if filename in self.file_counter:
            self.file_counter[filename] += 1
            name, ext = filename.rsplit('.', 1)
            filename = f"{name}_{self.file_counter[filename]}.{ext}"
        else:
            self.file_counter[filename] = 0
        
        # Create full file path
        file_path = self.domain_path / filename
        
        # Save HTML content
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Store local file path in item
            adapter['local_file_path'] = str(file_path)
            
            # Update URL mapping
            self.url_mapping[url] = {
                'local_file_path': str(file_path),
                'filename': filename,
                'title': adapter.get('title', ''),
                'timestamp': adapter.get('timestamp', datetime.now().isoformat()),
                'size_bytes': len(html_content.encode('utf-8'))
            }
            
            spider.logger.debug(f"Saved HTML: {url} -> {file_path}")
            
        except Exception as e:
            spider.logger.error(f"Failed to save HTML for {url}: {e}")
        
        return item
    
    def generate_filename(self, url):
        """Generate a safe filename from URL"""
        parsed = urlparse(url)
        
        # Start with the path
        path = parsed.path.strip('/')
        
        # If path is empty, use the domain
        if not path:
            path = parsed.netloc
        
        # Replace path separators with underscores
        path = path.replace('/', '_')
        
        # Remove or replace invalid filename characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', path)
        
        # Remove multiple underscores
        filename = re.sub(r'_+', '_', filename)
        
        # Add query parameters if they exist (truncated)
        if parsed.query:
            query_hash = str(hash(parsed.query))[-6:]  # Last 6 digits of hash
            filename += f"_q{query_hash}"
        
        # Ensure filename is not too long (max 200 chars before extension)
        if len(filename) > 200:
            filename = filename[:200]
        
        # Ensure filename doesn't end with underscore
        filename = filename.rstrip('_')
        
        # If filename is empty, use a default
        if not filename:
            filename = 'index'
        
        # Add .html extension
        return f"{filename}.html"