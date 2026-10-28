import scrapy
import json
import sys
from ...items import ProductDetailsItem
from ...database.db import get_connection


class RetailerDetailsSpider(scrapy.Spider):

    name = "toqueen_details"
    currentversion = 1

    async def start(self):

        print()
        print("############################################")
        print("######## TOQUEEN DETAILS SPIDER START ########")
        print("############################################")

        # -----------------------------------------
        # DATABASE CONNECTION
        # -----------------------------------------

        self.connection = get_connection()
        self.cursor = self.connection.cursor()
        site_code = "QUEENOM"
        product_table = f"{site_code}_Products"

        print("DATABASE CONNECTED", flush=True)

        query = f"SELECT ProductId, ProductURL FROM {product_table} WITH (NOLOCK) WHERE Version = ? AND ISNULL(Description, '') = '' and ISNew = 1 ORDER BY ProductId"

        self.cursor.execute(query, (self.currentversion,))

        rows = self.cursor.fetchall()

        print("TOTAL PRODUCTS FOR DETAILS:", len(rows), flush=True)
        # exit()

        # -----------------------------------------
        # REQUEST EACH PRODUCT
        # -----------------------------------------

        for row in rows:

            product_id = row.ProductId
            product_url = row.ProductURL

            yield scrapy.Request(
                url=product_url,
                callback=self.parse,
                meta={
                    "product_id": product_id,
                    "product_url": product_url,
                    "product_table": product_table,
                    "site_code": site_code,
                    "currentversion": self.currentversion,
                },
                dont_filter=True,
            )

    def parse(self, response):

        product_id = response.meta["product_id"]
        product_url = response.meta["product_url"]
        product_table = response.meta["product_table"]
        site_code = response.meta["site_code"]
        currentversion = response.meta["currentversion"]

        print()
        print("############################################")
        print("######## PRODUCT DETAILS RESPONSE ##########")
        print("############################################")

        print("PRODUCT ID:", product_id, flush=True)
        print("STATUS:", response.status, flush=True)
        print("URL:", response.url, flush=True)
        print("RESPONSE LENGTH:", len(response.text), flush=True)

        if not response.text:

            print("EMPTY RESPONSE:", product_url, flush=True)

            return

        # =================================================
        # DESCRIPTION
        # =================================================

        description = (
            response.xpath(
                '//details[starts-with(@id, "tab-description")]'
                # '//div[contains(@class, "product-description")]'
            ).get()
            or ""
        ).strip()

        # =================================================
        # PRINT EXTRACTED DATA
        # =================================================

        print()
        print("============================================")
        print("######## EXTRACTED PRODUCT DETAILS ########")
        print("============================================")

        print("PRODUCT ID:", product_id, flush=True)

        print("DESCRIPTION:", description, flush=True)

        print("============================================")
        # exit()

        # =================================================
        # SEND DATA TO PIPELINE
        # =================================================

        yield ProductDetailsItem(
            product_id=product_id,
            description=description,
            product_table=product_table,
            site_code=site_code,
            currentversion=currentversion,
        )
