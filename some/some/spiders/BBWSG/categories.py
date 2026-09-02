import scrapy
import sys

from ...database.db import get_connection
from ...items import CategoryItem
from ...database import site_config


class BBWAUCategorySpider(scrapy.Spider):

    name = "bbwau_categories"

    def start_requests(self):

        site_id = 903
        connection = get_connection()
        cursor = connection.cursor()

        try:

            site_config.load_site_config()

            print(site_config.SITE_ID)
            print(site_config.SITE_CODE)
            print(site_config.CATEGORY_TABLE)
            print(site_config.PRODUCT_TABLE)
            print(site_config.ARCHIVE_TABLE)
            site_id = site_config.SITE_ID
            site_code = site_config.SITE_CODE
            category_table = site_config.CATEGORY_TABLE
            archive_table = site_config.ARCHIVE_TABLE

            # Start from your main/domain URL
            start_url = "https://www.bathandbodyworks.com.au/"

            yield scrapy.Request(
                url=start_url,
                callback=self.parse,
                meta={
                    "site_code": site_code,
                },
            )

        finally:
            cursor.close()
            connection.close()

    def parse(self, response):

        site_code = response.meta["site_code"]
        print("\n================================")
        print("CATEGORY PAGE:", response.url)
        print("STATUS:", response.status)
        print("================================")

        # ------------------------------------------------
        # MAIN CATEGORY
        # ParentCategoryID = 1
        # ------------------------------------------------

        links = response.css("a::attr(href)").getall()

        for href in links:

            category_url = response.urljoin(href)
            category_name = response.css(f'a[href="{href}"]::text').get()

            if not category_name:
                continue

            category_name = category_name.strip()

            if not category_name:
                continue

            item = CategoryItem()

            item["category_url"] = category_url
            item["category_name"] = category_name
            item["parent_category_id"] = 1
            item["site_code"] = site_code

            print("CATEGORY:")
            print("NAME  :", category_name)
            print("URL   :", category_url)
            print("PARENT:", 1)

            yield item
