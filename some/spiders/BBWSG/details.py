import scrapy
import json
import sys
from ...items import ProductDetailsItem
from ...database.db import get_connection


class BBWITDetailsSpider(scrapy.Spider):

    name = "bbwsg_details"

    allowed_domains = ["bathandbodyworks.com.sg"]

    currentversion = 1

    async def start(self):

        print()
        print("############################################")
        print("######## BBWIT DETAILS SPIDER START ########")
        print("############################################")

        # -----------------------------------------
        # DATABASE CONNECTION
        # -----------------------------------------

        self.connection = get_connection()
        self.cursor = self.connection.cursor()
        site_code = "BBWTH"
        product_table = f"{site_code}_Products"

        print("DATABASE CONNECTED", flush=True)

        # -----------------------------------------
        # SELECT PRODUCTS
        # Same logic as PHP
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

            # print()
            # print("PRODUCT ID:", product_id, flush=True)
            # print("PRODUCT URL:", product_url, flush=True)

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

        if not response.text:

            print("EMPTY RESPONSE:", product_url, flush=True)

            return

        # =================================================
        # DESCRIPTION
        # =================================================

        description = ""

        description_parts = (
            response.css(
                "div.description-and-detail.accordion div.value.content.collapse"
            )
            .xpath("./node()")
            .getall()
        )

        if description_parts:
            description = "".join(description_parts).strip()

        # =================================================
        # JSON-LD
        # BRAND / RATING / REVIEW COUNT
        # =================================================

        brand = ""

        rating = ""

        json_ld_list = response.css('script[type="application/ld+json"]::text').getall()

        brand = ""
        multiimage_url = []
        product = None

        for json_text in json_ld_list:

            if not json_text:
                continue

            try:
                data = json.loads(json_text)
            except Exception as e:
                print("JSON-LD ERROR:", e, flush=True)
                continue

            # WebPage -> mainEntity
            main_entity = data.get("mainEntity")

            if not isinstance(main_entity, dict):
                continue

            # Check mainEntity type
            if main_entity.get("@type") != "Product":
                continue

            print("######## PRODUCT MAIN ENTITY FOUND ########", flush=True)

            product = main_entity

            # BRAND
            brand_data = product.get("brand")

            if isinstance(brand_data, dict):
                brand = brand_data.get("name", "")
            elif isinstance(brand_data, str):
                brand = brand_data

            # IMAGES
            images = product.get("image", [])

            if isinstance(images, str):
                images = [images]

            if isinstance(images, list):
                multiimage_url = [
                    image.strip()
                    for image in images
                    if isinstance(image, str) and image.strip()
                ]

            # Convert list to database string
            multiimage_url = " | ".join(multiimage_url)

            print("BRAND:", brand, flush=True)
            print("MULTI IMAGES:", multiimage_url, flush=True)

            break

        # =================================================
        # CLEAN VALUES
        # =================================================

        # description = description.strip() if description else ""

        brand = str(brand).strip() if brand else ""

        # rating = str(rating).strip() if rating else ""

        # review_count = str(review_count).strip() if review_count else ""

        # ingredients = ingredients.strip() if ingredients else ""

        # ingredients_plaintext = (ingredients_plaintext.strip() if ingredients_plaintext else "")

        # nutrition = nutrition.strip() if nutrition else ""

        # nutrition_plaintext = nutrition_plaintext.strip() if nutrition_plaintext else ""

        # multiimage_url = multiimage_url.strip() if multiimage_url else ""

        brand = brand.replace("'", '"')
        description = description.replace("'", '"')

        # =================================================
        # PRINT EXTRACTED DATA
        # =================================================

        print()
        print("============================================")
        print("######## EXTRACTED PRODUCT DETAILS ########")
        print("============================================")

        print("PRODUCT ID:", product_id, flush=True)

        print("DESCRIPTION:", description[:300], flush=True)

        print("BRAND:", brand, flush=True)

        # print("RATING:", rating, flush=True)

        # print("REVIEW COUNT:", review_count, flush=True)

        # print("INGREDIENTS:", ingredients[:300], flush=True)

        # print("INGREDIENTS PLAIN:", ingredients_plaintext[:300], flush=True)

        # print("NUTRITION:", nutrition[:300], flush=True)

        # print("NUTRITION PLAIN:", nutrition_plaintext[:300], flush=True)

        print("MULTI IMAGE URL:", multiimage_url, flush=True)

        print("============================================")
        # exit()

        # =================================================
        # SEND DATA TO PIPELINE
        # =================================================

        yield ProductDetailsItem(
            product_id=product_id,
            description=description,
            brand=brand,
            multiimage_url=multiimage_url,
            product_table=product_table,
        )

    def closed(self, reason):

        print()
        print("############################################")
        print("######## BBWIT DETAILS SPIDER CLOSED #######")
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
