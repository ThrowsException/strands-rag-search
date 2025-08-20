import scrapy
from scrapy import Field
from itemadapter import ItemAdapter


class PageItem(scrapy.Item):
    url = Field()
    title = Field()
    content = Field()
    links = Field()
    status_code = Field()
    depth = Field()
    meta_description = Field()
    meta_keywords = Field()
    headings = Field()
    timestamp = Field()
    domain = Field()
    html_content = Field()  # Raw HTML content
    local_file_path = Field()  # Path to saved HTML file