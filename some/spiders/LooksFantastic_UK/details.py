import scrapy
import json
import sys
import re
from ...items import ProductDetailsItem
from ...database.db import get_connection


class LOOKSUKDetailsSpider(scrapy.Spider):

    name = "looks_details"

    allowed_domains = ["lookfantastic.com"]

    currentversion = 2

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
        site_code = "LOOKSUK"
        product_table = f"{site_code}_Products"
        currentversion = self.currentversion

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
            # product_url = "https://www.lookfantastic.com/p/natasha-denona-travel-brush-set-and-makeup-pouch/13974363/"

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
                    "site_code": site_code,
                    "currentversion": currentversion,
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

        description_container = response.css(
            "#product-description-0 .attribute-content"
        )

        if description_container:

            # Get complete HTML including <p>, <strong>, <br>, etc.
            description_parts = description_container.xpath("./node()").getall()

            description = "".join(description_parts).strip()

        print("DESCRIPTION LENGTH:", len(description), flush=True)
        # print("DESCRIPTION LENGTH:", description, flush=True)
        # exit()

        # =================================================
        # PRODUCT VISIT APPLICATION JSON
        # =================================================

        # product_script = response.css(
        #     'script[data-track="productVisit"][data-track-type="onload"]::text'
        # ).get()
        product_script = response.xpath(
            '//script[@data-track="productVisit"]/text()'
        ).get()

        print("PRODUCT VISIT SCRIPT FOUND:", bool(product_script), flush=True)

        brand = ""
        rating = ""
        review_count = ""

        if product_script:

            print("######## PRODUCT VISIT SCRIPT FOUND ########", flush=True)

            marker = "const productsObj ="

            start = product_script.find(marker)

            print("START POSITION:", start, flush=True)

            if start != -1:

                # Get everything after:
                # const productsObj =
                json_text = product_script[start + len(marker) :]

                # Remove everything after the JSON object
                json_text = json_text.split(";", 1)[0].strip()

                print("JSON TEXT:", json_text, flush=True)

                try:
                    products_obj = json.loads(json_text)

                    print("PRODUCT JSON LOADED", flush=True)

                    # Get first product
                    product_data = next(iter(products_obj.values()))

                    brand = product_data.get("item_brand", "")
                    rating = product_data.get("averageScore", "")
                    review_count = product_data.get("reviewsTotal", "")

                except Exception as e:
                    print("PRODUCT JSON ERROR:", e, flush=True)

        print("BRAND:", brand, flush=True)
        print("RATING:", rating, flush=True)
        print("REVIEW COUNT:", review_count, flush=True)
        # exit()
        # =================================================
        # MULTI IMAGES
        # =================================================
        srcsets = response.xpath("//picture/source/@srcset").getall()

        multiimages = []

        for srcset in srcsets:

            print("RAW SRCSET:", repr(srcset), flush=True)

            parts = srcset.split(",")

            for part in parts:
                part = part.strip()

                if part.endswith("2x"):
                    image_url = part[:-2].strip()

                    if image_url and image_url not in multiimages:
                        multiimages.append(image_url)

        multiimage_url = " | ".join(multiimages)

        print("MULTIIMAGE:", multiimage_url, flush=True)
        # exit()
        brand = brand.replace("'", '"')
        description = description.replace("'", '"')
        # =================================================
        # FINAL DEBUG
        # =================================================

        print("========================================", flush=True)

        print("FINAL BRAND:", brand, flush=True)

        print("FINAL RATING:", rating, flush=True)

        print("FINAL REVIEW COUNT:", review_count, flush=True)

        print("FINAL DESCRIPTION LENGTH:", len(description), flush=True)

        # print("FINAL IMAGE COUNT:", len(multiimage_list), flush=True)

        print("FINAL MULTI IMAGE URL:", multiimage_url, flush=True)

        print("========================================", flush=True)
        # exit()

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
            rating=rating,
            product_total_ratings=review_count,
            site_code=site_code,
            currentversion=currentversion,
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
