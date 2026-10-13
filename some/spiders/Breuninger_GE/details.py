import scrapy
import json
import sys
import re
from ...items import ProductDetailsItem
from ...database.db import get_connection


class BREUDetailsSpider(scrapy.Spider):

    name = "breu_details"
    allowed_domains = ["https://www.breuninger.com/de/"]
    currentversion = 1

    async def start(self):

        print()
        print("############################################")
        print("######## BREU DETAILS SPIDER START ########")
        print("############################################")

        # -----------------------------------------
        # DATABASE CONNECTION
        # -----------------------------------------

        self.connection = get_connection()
        self.cursor = self.connection.cursor()
        site_code = "BREUGE"
        product_table = f"{site_code}_Products"

        print("DATABASE CONNECTED", flush=True)

        # -----------------------------------------

        # SELECT PRODUCTS
        # -----------------------------------------

        query = f"SELECT ProductId, ProductURL FROM {product_table} WITH (NOLOCK) WHERE Version = ? AND ISNULL(Description, '') = '' AND ISNew = 1 ORDER BY ProductId"

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

        # -------------------------------------------------
        # IMPORTANT
        #
        # Zyte fallback is handled in middleware.
        #
        # Therefore this response should already contain
        # the normal HTML OR the Zyte HTML.
        # -------------------------------------------------
        description = None
        ingredients = None
        nutrition = None
        brand = None
        rating = None
        ProductRating = None
        product_total_ratings = None
        multiimage_url = None
        # ============================================================
        # DESCRIPTION
        # ============================================================

        description = (
            response.css("div[data-test-ents-static-description] > div")
            .xpath("string(.)")
            .get()
        )

        if description:
            description = " ".join(description.split()).strip()

        # ============================================================
        # INGREDIENTS
        # ============================================================

        ingredients = (
            response.css("div[data-test-ents-static-ingredients] > div")
            .xpath("string(.)")
            .get()
        )

        if ingredients:
            ingredients = " ".join(ingredients.split()).strip()

        # ============================================================
        # MULTI IMAGES
        # ============================================================

        multiimages = response.css(
            "div.ents-image-view__desktop "
            "div.ents-image-view__entry img.ents-image-view__image::attr(src)"
        ).getall()

        # Remove duplicates while preserving order
        multiimages = list(dict.fromkeys(multiimages))
        multiimage_url = " | ".join(multiimages)

        print("DESCRIPTION:", description, flush=True)
        print("INGREDIENTS:", ingredients, flush=True)
        print("MULTIIMAGE:", multiimage_url, flush=True)
        # exit()
        item = ProductDetailsItem()

        item["product_id"] = product_id
        item["product_table"] = product_table
        item["description"] = description
        item["ingredients"] = ingredients
        item["nutrition"] = nutrition
        item["brand"] = brand
        item["rating"] = rating
        item["ProductRating"] = ProductRating
        item["product_total_ratings"] = product_total_ratings
        item["multiimage_url"] = multiimage_url
        yield item

    def closed(self, reason):

        print()
        print("############################################")
        print("######## BREU DETAILS SPIDER CLOSED #######")
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
