BOT_NAME = 'open_rag_search'

SPIDER_MODULES = ['open_rag_search.spiders']
NEWSPIDER_MODULE = 'open_rag_search.spiders'

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure pipelines
ITEM_PIPELINES = {
    'open_rag_search.pipelines.DuplicatesPipeline': 200,
    'open_rag_search.pipelines.ProcessPagePipeline': 300,
    'open_rag_search.pipelines.HtmlDownloadPipeline': 350,  # Save HTML before other processing
    'open_rag_search.pipelines.JsonPipeline': 400,
    'open_rag_search.pipelines.StatsPipeline': 500,
}

# Configure delays and concurrency
DOWNLOAD_DELAY = 1
RANDOMIZE_DOWNLOAD_DELAY = 0.5
CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 8

# AutoThrottle settings
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0
AUTOTHROTTLE_DEBUG = False

# HTTP caching
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 3600
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_IGNORE_HTTP_CODES = [503, 504, 505, 500, 403, 404, 408, 429]

# User agent
USER_AGENT = 'open_rag_search (+http://www.yourdomain.com)'

# Request headers
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en',
}

# Retry settings
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429]

# Timeout settings
DOWNLOAD_TIMEOUT = 30

# Depth limit
DEPTH_LIMIT = 3
DEPTH_PRIORITY = 1

# Log level
LOG_LEVEL = 'INFO'

# Output file settings
JSON_OUTPUT_FILE = 'crawl_results.json'
CSV_OUTPUT_FILE = 'crawl_results.csv'

# HTML download settings
HTML_DOWNLOAD_FOLDER = 'html_downloads'

# Memory usage optimization
MEMUSAGE_ENABLED = True
MEMUSAGE_LIMIT_MB = 2048
MEMUSAGE_WARNING_MB = 1024

# DNS settings
DNSCACHE_ENABLED = True
DNSCACHE_SIZE = 10000
DNS_TIMEOUT = 60

# Extensions
EXTENSIONS = {
    'scrapy.extensions.telnet.TelnetConsole': None,
    'scrapy.extensions.memusage.MemoryUsage': 1,
    'scrapy.extensions.closespider.CloseSpider': 1,
}

# Close spider settings
CLOSESPIDER_TIMEOUT = 3600  # 1 hour timeout
CLOSESPIDER_ITEMCOUNT = 1000  # Stop after 1000 items
CLOSESPIDER_PAGECOUNT = 1000  # Stop after 1000 pages
CLOSESPIDER_ERRORCOUNT = 50   # Stop after 50 errors

# Twisted reactor settings
REACTOR_THREADPOOL_MAXSIZE = 20

# Request fingerprinting
REQUEST_FINGERPRINTER_IMPLEMENTATION = '2.7'

# Telnet Console (disabled for security)
TELNETCONSOLE_ENABLED = False

# Feed exports (alternative output formats)
FEEDS = {
    'results.json': {
        'format': 'json',
        'encoding': 'utf8',
        'store_empty': False,
        'indent': 2,
    },
    'results.csv': {
        'format': 'csv',
        'encoding': 'utf8',
        'store_empty': False,
    },
    'results.jl': {
        'format': 'jsonlines',
        'encoding': 'utf8',
        'store_empty': False,
    },
}