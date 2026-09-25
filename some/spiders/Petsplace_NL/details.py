import scrapy
import json
import sys
import re
from ...items import ProductDetailsItem
from ...database.db import get_connection


class PETSDetailsSpider(scrapy.Spider):

    name = "pets_details"
    allowed_domains = ["https://www.petsplace.nl"]
    currentversion = 1

    async def start(self):

        print()
        print("############################################")
        print("######## PETS DETAILS SPIDER START ########")
        print("############################################")

        # -----------------------------------------
        # DATABASE CONNECTION
        # -----------------------------------------

        self.connection = get_connection()
        self.cursor = self.connection.cursor()
        site_code = "PETSNL"
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
        product_total_ratings = None
        multiimage_url = None
        if not response.text:

            print("EMPTY RESPONSE:", product_url, flush=True)

            return

        json_ld = response.css('script[type="application/ld+json"]::text').getall()

        for json_text in json_ld:

            try:
                data = json.loads(json_text)

                product_type = data.get("@type", "")

                if not str(product_type).endswith("Product"):
                    continue

                description = data.get("description")

                brand_data = data.get("brand")

                if isinstance(brand_data, dict):
                    brand = brand_data.get("name")
                else:
                    brand = brand_data

                aggregate_rating = data.get("aggregateRating")

                if aggregate_rating:
                    rating = aggregate_rating.get("ratingValue")
                    product_total_ratings = aggregate_rating.get("reviewCount")

                break

            except Exception as e:
                print("JSON-LD ERROR:", e, flush=True)

        ProductRating = rating
        print("description:", description, flush=True)
        print("brand:", brand, flush=True)
        print("rating:", rating, flush=True)
        print("product_total_ratings:", product_total_ratings, flush=True)
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
        print("######## PETS DETAILS SPIDER CLOSED #######")
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
