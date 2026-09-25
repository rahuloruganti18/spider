import scrapy
import json
import sys
import re
from ...items import ProductDetailsItem
from ...database.db import get_connection


class LOOKSUKDetailsSpider(scrapy.Spider):

    name = "shoprite_details"

    allowed_domains = ["lookfantastic.com"]

    currentversion = 1

    async def start(self):

        print()
        print("############################################")
        print("######## LOOKSUK DETAILS SPIDER START ########")
        print("############################################")

        # -----------------------------------------
        # DATABASE CONNECTION
        # -----------------------------------------

        self.connection = get_connection()
        self.cursor = self.connection.cursor()
        site_code = "SHOPRITE"
        product_table = f"{site_code}_Products"

        print("DATABASE CONNECTED", flush=True)

        # -----------------------------------------
        # SELECT PRODUCTS
        # -----------------------------------------

        query = f"SELECT ProductId, ProductURL FROM {product_table} WITH (NOLOCK) WHERE Version = ? AND ISNULL(Description, '') = '' AND ISNew = 1 ORDER BY ProductId ASC"

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
                },
                dont_filter=True,
            )

    def parse(self, response):

        product_id = response.meta["product_id"]
        product_url = response.meta["product_url"]
        product_table = response.meta["product_table"]

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

        description = ""
        # INGREDIENTS
        ingredients = response.css(
            'div[data-testid="PdpIngredientsTestId"] *::text'
        ).getall()

        ingredients = " ".join(x.strip() for x in ingredients if x.strip())

        # DESCRIPTION
        description = (
            response.css('div[class*="PdpDescription1"]')
            .xpath(".//text()[not(ancestor::h3)]")
            .getall()
        )

        description = " ".join(x.strip() for x in description if x.strip())

        # NUTRITION
        nutrition_items = response.css('div[data-testid="nutrientItem-div-testId"]')

        nutrition = []

        for nutrient in nutrition_items:

            value = nutrient.css("h3::text").get()
            name = nutrient.css("div::text").get()

            if value and name:
                nutrition.append(f"{name.strip()}: {value.strip()}")

        nutrition = " | ".join(nutrition)

        print("INGREDIENTS:", ingredients, flush=True)
        print("DESCRIPTION:", description, flush=True)
        print("NUTRITION:", nutrition, flush=True)
        # exit()

        # =================================================
        # SEND DATA TO PIPELINE
        # =================================================

        yield ProductDetailsItem(
            product_id=product_id,
            description=description,
            ingredients=ingredients,
            nutrition=nutrition,
            product_table=product_table,
        )

    def closed(self, reason):

        print()
        print("############################################")
        print("######## LOOKSUK DETAILS SPIDER CLOSED #######")
        print("REASON:", reason)
        print("############################################")

        try:

            if self.cursor:

                self.cursor.close()

            if self.connection:

                self.connection.close()

            print("DATABASE CONNECTION CLOSED", flush=True)

        except Exception as e:

            print("DATABASE CLOSE ERROR:", e, flush=True)
