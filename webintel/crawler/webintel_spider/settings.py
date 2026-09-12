BOT_NAME = "webintel"
SPIDER_MODULES = ["webintel_spider.spiders"]
NEWSPIDER_MODULE = "webintel_spider.spiders"
ROBOTSTXT_OBEY = True
DOWNLOAD_DELAY = 1
CONCURRENT_REQUESTS = 4
USER_AGENT = "WebIntelBot/1.0 (respectful research crawler)"
ITEM_PIPELINES = {"webintel_spider.pipelines.WebIntelPipeline": 300}
