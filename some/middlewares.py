# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

"""from scrapy import signals

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


class SomeSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    async def process_start(self, start):
        # Called with an async iterator over the spider start() method or the
        # matching method of an earlier spider middleware.
        async for item_or_request in start:
            yield item_or_request

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class SomeDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)"""

# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import base64
import logging
import requests

from scrapy import signals
from scrapy.http import HtmlResponse
from itemadapter import ItemAdapter

# ============================================================
# SPIDER MIDDLEWARE
# ============================================================


class SomeSpiderMiddleware:

    @classmethod
    def from_crawler(cls, crawler):

        s = cls()

        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)

        return s

    def process_spider_input(self, response, spider):

        return None

    def process_spider_output(self, response, result, spider):

        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):

        pass

    async def process_start(self, start):

        async for item_or_request in start:
            yield item_or_request

    def spider_opened(self, spider):

        spider.logger.info("Spider opened: %s", spider.name)


# ============================================================
# DOWNLOADER MIDDLEWARE
# ============================================================


class SomeDownloaderMiddleware:

    # --------------------------------------------------------
    # CREATE MIDDLEWARE
    # --------------------------------------------------------

    @classmethod
    def from_crawler(cls, crawler):

        s = cls()

        s.crawler = crawler
        s.settings = crawler.settings

        # Get Zyte API key from settings.py
        s.zyte_api_key = crawler.settings.get("ZYTE_API_KEY")

        # Create logger
        s.logger = logging.getLogger(__name__)

        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)

        return s

    # --------------------------------------------------------
    # SPIDER OPENED
    # --------------------------------------------------------

    def spider_opened(self, spider):

        print("\n########################################", flush=True)

        print("######## DOWNLOADER MIDDLEWARE OPENED ########", flush=True)

        print("SPIDER:", spider.name, flush=True)

        print("ZYTE KEY:", "FOUND" if self.zyte_api_key else "NOT FOUND", flush=True)

        print("########################################\n", flush=True)

        spider.logger.info("Downloader middleware opened")

        spider.logger.info(
            "ZYTE API KEY: %s", "FOUND" if self.zyte_api_key else "NOT FOUND"
        )

    # --------------------------------------------------------
    # NORMAL REQUEST
    # --------------------------------------------------------

    def process_request(self, request, spider):

        print("\n######## NORMAL REQUEST ########", flush=True)

        print("URL:", request.url, flush=True)

        spider.logger.info("NORMAL REQUEST: %s", request.url)

        # IMPORTANT:
        # Returning None means:
        # "Continue with the normal Scrapy downloader."

        return None

    # --------------------------------------------------------
    # NORMAL RESPONSE
    # --------------------------------------------------------

    def process_response(self, request, response, spider):

        print("\n######## NORMAL RESPONSE RECEIVED ########", flush=True)

        print("URL:", response.url, flush=True)

        print("STATUS:", response.status, flush=True)

        # print("STATUS:", response.text, flush=True)

        print("RESPONSE LENGTH:", len(response.body), flush=True)

        spider.logger.info(
            "NORMAL RESPONSE: URL=%s STATUS=%s LENGTH=%s",
            response.url,
            response.status,
            len(response.body),
        )

        # ----------------------------------------------------
        # CHECK IF NORMAL RESPONSE IS GOOD
        # ----------------------------------------------------

        if self.is_response_good(response):

            print("######## NORMAL RESPONSE IS GOOD ########", flush=True)

            spider.logger.info("NORMAL RESPONSE IS GOOD: %s", response.url)

            # Send normal response to spider.parse()
            return response

        # ----------------------------------------------------
        # NORMAL RESPONSE IS BLOCKED / BAD
        # ----------------------------------------------------

        print("######## NORMAL RESPONSE IS BLOCKED/BAD ########", flush=True)

        print("STATUS:", response.status, flush=True)

        print("######## CALLING ZYTE ########", flush=True)

        spider.logger.warning(
            "NORMAL RESPONSE BAD/BLOCKED: URL=%s STATUS=%s",
            response.url,
            response.status,
        )

        # ----------------------------------------------------
        # CALL ZYTE
        # ----------------------------------------------------

        zyte_response = self.get_zyte_response(request, response.url, spider)

        # ----------------------------------------------------
        # ZYTE SUCCESS
        # ----------------------------------------------------

        if zyte_response is not None:

            print("######## ZYTE RESPONSE SUCCESS ########", flush=True)

            print("ZYTE URL:", zyte_response.url, flush=True)

            print("ZYTE STATUS:", zyte_response.status, flush=True)

            print("ZYTE HTML LENGTH:", len(zyte_response.body), flush=True)

            spider.logger.info(
                "ZYTE RESPONSE SUCCESS: URL=%s LENGTH=%s",
                zyte_response.url,
                len(zyte_response.body),
            )

            # This goes to spider.parse()
            return zyte_response

        # ----------------------------------------------------
        # ZYTE ALSO FAILED
        # ----------------------------------------------------

        print("######## ZYTE FAILED - RETURNING ORIGINAL RESPONSE ########", flush=True)

        spider.logger.error("ZYTE FAILED: %s", response.url)

        # Return original response
        return response

    # --------------------------------------------------------
    # CHECK NORMAL RESPONSE
    # --------------------------------------------------------

    def is_response_good(self, response):

        # HTTP status codes that should trigger Zyte

        blocked_status_codes = {
            403,
            429,
            500,
            502,
            503,
            504,
        }

        # ----------------------------------------------------
        # BAD STATUS
        # ----------------------------------------------------

        if response.status in blocked_status_codes:

            return False

        # ----------------------------------------------------
        # EMPTY RESPONSE
        # ----------------------------------------------------

        if not response.body:

            return False

        # ----------------------------------------------------
        # EMPTY TEXT
        # ----------------------------------------------------

        try:

            text = response.text.strip()

        except Exception:

            return False

        if not text:

            return False

        # ----------------------------------------------------
        # CHECK COMMON BLOCK PAGE TEXT
        # ----------------------------------------------------

        lower_text = text[:10000].lower()

        blocked_words = [
            "request rejected",
            "access denied",
            "access is denied",
            "forbidden",
            "temporarily blocked",
            "unusual traffic",
            "bot detected",
            "captcha",
            "verify you are human",
            "robot check",
            "security check",
        ]

        for word in blocked_words:

            if word in lower_text:

                return False

        # ----------------------------------------------------
        # RESPONSE LOOKS GOOD
        # ----------------------------------------------------

        return True

    # --------------------------------------------------------
    # ZYTE API
    # --------------------------------------------------------

    def get_zyte_response(self, request, url, spider):

        print("\n######## ZYTE REQUEST START ########", flush=True)

        print("ZYTE URL:", url, flush=True)

        spider.logger.info("ZYTE REQUEST START: %s", url)

        # ----------------------------------------------------
        # CHECK API KEY
        # ----------------------------------------------------

        if not self.zyte_api_key:

            print("######## ZYTE API KEY NOT FOUND ########", flush=True)

            spider.logger.error("ZYTE_API_KEY NOT FOUND IN settings.py")

            return None

        try:

            # ------------------------------------------------
            # ZYTE API REQUEST
            # ------------------------------------------------

            api_response = requests.post(
                "https://api.zyte.com/v1/extract",
                auth=(self.zyte_api_key, ""),
                json={
                    "url": url,
                    "httpResponseBody": True,
                },
                timeout=90,
            )

            # ------------------------------------------------
            # ZYTE API STATUS
            # ------------------------------------------------

            print(
                "######## ZYTE API STATUS ########",
                api_response.status_code,
                flush=True,
            )

            spider.logger.info("ZYTE API STATUS: %s", api_response.status_code)

            # ------------------------------------------------
            # ZYTE API FAILED
            # ------------------------------------------------

            if api_response.status_code != 200:

                print("######## ZYTE API FAILED ########", flush=True)

                print("ZYTE ERROR:", api_response.text[:1000], flush=True)

                spider.logger.error(
                    "ZYTE API FAILED: STATUS=%s RESPONSE=%s",
                    api_response.status_code,
                    api_response.text[:1000],
                )

                return None

            # ------------------------------------------------
            # CONVERT JSON
            # ------------------------------------------------

            data = api_response.json()

            # ------------------------------------------------
            # GET BASE64 BODY
            # ------------------------------------------------

            encoded_body = data.get("httpResponseBody")

            if not encoded_body:

                print("######## ZYTE RETURNED NO HTML ########", flush=True)

                spider.logger.error("ZYTE RETURNED NO httpResponseBody: %s", url)

                return None

            # ------------------------------------------------
            # DECODE BASE64
            # ------------------------------------------------

            html_body = base64.b64decode(encoded_body)

            print("######## ZYTE HTML RECEIVED ########", flush=True)

            print("HTML LENGTH:", len(html_body), flush=True)

            spider.logger.info(
                "ZYTE HTML RECEIVED: URL=%s LENGTH=%s", url, len(html_body)
            )

            # ------------------------------------------------
            # GET ZYTE STATUS CODE
            # ------------------------------------------------

            zyte_status = data.get("statusCode", 200)

            # ------------------------------------------------
            # CREATE SCRAPY RESPONSE
            # ------------------------------------------------

            new_response = HtmlResponse(
                url=data.get("url", url),
                status=zyte_status,
                headers=response_headers_to_scrapy(data.get("httpResponseHeaders", [])),
                body=html_body,
                encoding="utf-8",
                request=request,
            )

            # ------------------------------------------------
            # MARK RESPONSE AS ZYTE
            # ------------------------------------------------

            new_response.meta["zyte_response"] = True

            new_response.meta["original_url"] = url

            print("######## SCRAPY ZYTE RESPONSE CREATED ########", flush=True)

            spider.logger.info("SCRAPY ZYTE RESPONSE CREATED: %s", url)

            return new_response

        except requests.RequestException as e:

            print("######## ZYTE REQUEST ERROR ########", flush=True)

            print("ERROR:", str(e), flush=True)

            spider.logger.exception("ZYTE REQUEST ERROR: %s", url)

            return None

        except Exception as e:

            print("######## ZYTE ERROR ########", flush=True)

            print("ERROR:", str(e), flush=True)

            spider.logger.exception("ZYTE ERROR: %s", url)

            return None

    # --------------------------------------------------------
    # DOWNLOADER EXCEPTION
    # --------------------------------------------------------

    def process_exception(self, request, exception, spider):

        print("\n######## NORMAL REQUEST EXCEPTION ########", flush=True)

        print("URL:", request.url, flush=True)

        print("ERROR:", str(exception), flush=True)

        spider.logger.error(
            "NORMAL REQUEST EXCEPTION: URL=%s ERROR=%s", request.url, str(exception)
        )

        # ----------------------------------------------------
        # NORMAL REQUEST ITSELF FAILED
        # TRY ZYTE
        # ----------------------------------------------------

        print("######## TRYING ZYTE AFTER EXCEPTION ########", flush=True)

        spider.logger.info("TRYING ZYTE AFTER EXCEPTION: %s", request.url)

        zyte_response = self.get_zyte_response(request, request.url, spider)

        # ----------------------------------------------------
        # ZYTE SUCCESS
        # ----------------------------------------------------

        if zyte_response is not None:

            print("######## ZYTE SUCCESS AFTER EXCEPTION ########", flush=True)

            spider.logger.info("ZYTE SUCCESS AFTER EXCEPTION: %s", request.url)

            return zyte_response

        # ----------------------------------------------------
        # ZYTE FAILED
        # ----------------------------------------------------

        print("######## ZYTE FAILED AFTER EXCEPTION ########", flush=True)

        spider.logger.error("ZYTE FAILED AFTER EXCEPTION: %s", request.url)

        return None


# ============================================================
# CONVERT ZYTE HEADERS
# ============================================================


def response_headers_to_scrapy(zyte_headers):

    headers = {}

    if not zyte_headers:

        return headers

    for header in zyte_headers:

        name = header.get("name")

        value = header.get("value")

        if name and value:

            headers[name.encode()] = value.encode()

    return headers
