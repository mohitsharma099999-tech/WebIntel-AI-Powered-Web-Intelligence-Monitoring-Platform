import scrapy
from ..items import WebIntelItem

class GenericSpider(scrapy.Spider):
    name = "generic"
    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "DOWNLOAD_DELAY": 1,
        "CONCURRENT_REQUESTS": 4,
        "USER_AGENT": "WebIntelBot/1.0 (respectful research crawler)"
    }

    def __init__(self, start_url=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not start_url:
            raise ValueError("start_url is required")
        self.start_urls = [start_url]

    def parse(self, response):
        item = WebIntelItem()
        item["url"] = response.url
        item["title"] = response.css("title::text").get()
        item["content"] = " ".join(response.css("body *::text").getall()).strip()
        yield item

        for link in response.css("a::attr(href)").getall():
            yield response.follow(link, callback=self.parse)
