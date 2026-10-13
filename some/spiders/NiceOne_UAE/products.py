import scrapy
from ...items import ProductItem, CategoryDetailsItem, archivedetails
import sys
import pyodbc
import json
import re

# from ...database import site_config
from ...database.db import get_connection
from ...database.site_config import get_site_config
from ...database.site_config import get_conversion_rate


class ExampleSpider(scrapy.Spider):

    print("######## EXAMPLE BBWIT FILE LOADED ########")

    name = "nice_prod"
    allow_domains = ["https://niceonesa.com/en"]

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "en-US,en;q=0.9,hi;q=0.8,fr;q=0.7",
        "cache-control": "max-age=0",
        "cookie": "_session=2a5d188d1bf5dd79c2382ba6b436a7ac; _offer_tab=%7B%22tab_id%22%3A%2227%22%2C%22title%22%3Anull%2C%22icon%22%3A%22https%3A%2F%2Fd1aq4ubbxe020v.cloudfront.net%2Fimage%2Fcatalog%2Fundefin%2F47581281_1787755535_4859d39201496178a399d46f9b207189.gif%22%2C%22icon_active%22%3A%22https%3A%2F%2Fd1aq4ubbxe020v.cloudfront.net%2Fimage%2Fcatalog%2Fundefin%2F47581281_1787755535_4859d39201496178a399d46f9b207189.gif%22%2C%22size%22%3A48%2C%22en_name%22%3A%22Saudi%20Brands%22%7D; _gcl_au=1.1.1835919253.1789987485; __utm_aff_lastChannel=; _tt_enable_cookie=1; _ttp=01M31S2XS98ZNNEV2NEYB55MWF_.tt.1.1789987485481; _scid=o4hd6ODc1M6mpVwEefs21JKdGXCwq57s; _fbp=fb.1.1789987485698.132398709430310950; th_external_id=96e939b28e1fc50aaa509ccd1b0b559f5b7a7e805395077f309df6cc19d9837c; _address=%7B%22short_name%22%3A%22%22%2C%22city%22%3A%22%22%2C%22country%22%3A%22Saudi%20Arabia%22%2C%22iso_code_2%22%3A%22%22%2C%22administrative_area_level_1%22%3A%22%22%2C%22lat%22%3A24.713552%2C%22long%22%3A46.675297%2C%22store_id%22%3A%22261%22%2C%22zone_id%22%3A%22261%22%2C%22formatted_address%22%3A%22Al%20Woroud%20%20-%20Riyadh%22%7D; _hide_cookie_consent=true; _gid=GA1.2.1734376176.1790578412; _sctr=1%7C1790533800000; _verify_token=eyJhbGciOiJIUzI1NiJ9.eyJ1cm46ZXhhbXBsZTpjbGFpbSI6dHJ1ZSwiZXhwIjoxNzkwNTc4OTkyfQ.rOPdreh-uWj37_WGDmnewJf2Dk_Wk0zwAV8zLTj133A; AMP_185e44a550=JTdCJTIyZGV2aWNlSWQlMjIlM0ElMjI2NTVmNGE3YS1iNjBiLTQwNjYtYWRkMi1iZmRmMjNkNmUyOGIlMjIlMkMlMjJzZXNzaW9uSWQlMjIlM0ExNzkwNTc4NDE2OTE0JTJDJTIyb3B0T3V0JTIyJTNBZmFsc2UlMkMlMjJsYXN0RXZlbnRUaW1lJTIyJTNBMTc5MDU3ODg1Njc0NCUyQyUyMmxhc3RFdmVudElkJTIyJTNBMTAlMkMlMjJwYWdlQ291bnRlciUyMiUzQTAlN0Q=; _ga=GA1.2.280833326.1789987485; __rtbh.lid=%7B%22eventType%22%3A%22lid%22%2C%22id%22%3A%22nkPh5iA4LPYN3Oqwfnh6%22%2C%22expiryDate%22%3A%222027-09-28T07%3A01%3A18.133Z%22%7D; _ga_TRJ7F9FM1R=GS2.1.s1790578411$o5$g1$t1790578878$j38$l0$h2139266532; _scid_r=tQhd6ODc1M6mpVwEefs21JKdGXCwq57sNONDHA; ttcsid=1790578411952::F7hRiy-xXN71GEc_yVHO.4.1790578879414.0::1.464562.467138::293086.6.328.231::457843.111.18; ttcsid_C7DDHSCRNSL79GUT97FG=1790578411952::81p5x14o2Acx_9t3Kfx9.3.1790578879414.1",
        "priority": "u=0, i",
        "sec-ch-ua": '"Google Chrome";v="153", "Not_A Brand";v="8", "Chromium";v="153"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36",
    }

    # start_urls = ["https://www.bathandbodyworks.com.au/body-care"]
    async def start(self):
        print("######## START REQUESTS ########", flush=True)

        connection = get_connection()
        cursor = connection.cursor()

        site_id = 845
        site = get_site_config(site_id)
        site_code = site["site_code"]
        category_table = site["category_table"]
        archive_table = site["archive_table"]
        # archive_table = f"{site_code}_Products_Archive"
        print(category_table)
        print(archive_table)
        # exit()
        max_vsel = f"SELECT TOP 1 RecordDate, Version FROM {archive_table} WITH (NOLOCK) ORDER BY RecordDate DESC"

        try:
            cursor.execute(max_vsel)
            max_vrow = cursor.fetchone()
            currentversion = (max_vrow.Version + 1) if max_vrow else 1
            print(f"Current Version: {currentversion}")

        except (pyodbc.ProgrammingError, Exception) as e:
            # Check if the error is due to a missing table
            if "Invalid object name" in str(e):
                # print("Table does not exist. Defaulting version to 1.")
                currentversion = 1
            else:
                print(f"An unexpected database error occurred: {e}")
                raise e

        # category_table = f"{site_code}_Categories"

        usdequal = get_conversion_rate(site_code)
        # print(usdequal)
        # exit()
        sql = f"SELECT SubCategoryID,SubCategoryName,SubCategoryURL,CurrentVersion FROM {category_table} WITH (NOLOCK) WHERE SubCategoryID NOT IN (SELECT ParentCategoryID FROM {category_table} WHERE ParentCategoryID IS NOT NULL) AND PriceICCategoryID IS NOT NULL ORDER BY SubCategoryID"

        cursor.execute(sql)
        rows = cursor.fetchall()
        print("TOTAL CATEGORY URLS:", len(rows))
        # exit()
        self.site_code = site_code
        self.currentversion = currentversion
        for row in rows:

            cat_id = row[0]
            category_name = row[1]
            category_url = row[2]
            category_version = row[3]

            print("REQUESTING CATEGORY:", category_name)
            print("URL:", category_url)
            if not category_url:
                print(f"SKIPPING CATEGORY: {category_name} - URL is empty", flush=True)
                continue
            if category_version is not None and category_version >= currentversion:

                print(
                    f"ALREADY CATEGORY DOWNLOADED: "
                    f"{category_name} | "
                    f"DB VERSION: {category_version} | "
                    f"CURRENT VERSION: {currentversion}"
                )
                continue

            yield scrapy.Request(
                url=category_url,
                headers=self.headers,
                callback=self.parse,
                meta={
                    "cat_id": cat_id,
                    "category_name": category_name,
                    "category_url": category_url,
                    "currentversion": currentversion,
                    "site_id": site_id,
                    "site_code": site_code,
                    "usdequal": usdequal,
                    "category_table": category_table,
                    "handle_httpstatus_all": True,
                    "product_count": 0,
                },
                dont_filter=True,
            )
        # exit()

        cursor.close()
        connection.close()

    def parse(self, response):

        print("\n======================================")
        print("Parse CURRENT PAGE:", response.url)
        print("STATUS:", response.status)
        # print("STATUS:", response.text)
        print("======================================")
        # exit()

        cat_id = response.meta["cat_id"]
        category_name = response.meta["category_name"]
        category_url = response.meta["category_url"]
        currentversion = response.meta["currentversion"]
        site_id = response.meta["site_id"]
        site_code = response.meta["site_code"]
        usdequal = response.meta["usdequal"]
        category_table = response.meta["category_table"]
        product_count = ""
        print("########################################page")

        json_ld = response.css('script[type="application/ld+json"]::text').getall()

        for json_text in json_ld:
            try:
                data = json.loads(json_text)

                # if data.get("@type") == "ItemList":
                #     print("ITEMLIST JSON FOUND")

                #     # Proceed with your ItemList processing here
                #     item_list = data
                # Process only ItemList JSON
                if data.get("@type") != "ItemList":
                    continue

                products = data.get("itemListElement", [])

                # Initialize count
                if product_count == "":
                    product_count = 0

                # Add products from current page
                product_count += len(
                    [
                        product
                        for product in products
                        if product.get("@type") == "Product"
                    ]
                )

                print("CURRENT PAGE PRODUCT COUNT:", len(products))
                print("TOTAL PRODUCT COUNT:", product_count)

                for product in products:
                    if product.get("@type") != "Product":
                        continue

                    offers = product.get("offers")

                    if isinstance(offers, dict) and offers.get("url"):
                        product_url = offers.get("url")
                    else:
                        product_url = product.get("url")

                    print("URL:", product_url)
                    print("-" * 50)

                    yield scrapy.Request(
                        url=product_url,
                        headers=self.headers,
                        callback=self.product_parse,
                        meta={
                            "cat_id": cat_id,
                            "category_name": category_name,
                            "category_url": category_url,
                            "currentversion": currentversion,
                            "site_id": site_id,
                            "site_code": site_code,
                            "usdequal": usdequal,
                            "category_table": category_table,
                            "handle_httpstatus_all": True,
                            "product_count": product_count,
                        },
                        dont_filter=True,
                    )

            except json.JSONDecodeError:
                continue

        # next_page = response.css("li.van-pagination__item--next a::attr(href)").get()
        next_page = response.css(
            "li.van-pagination__item--next:not(.van-pagination__item--disabled) a::attr(href)"
        ).get()

        if next_page:

            next_page = response.urljoin(next_page)

            print("NEXT PAGE:", next_page, flush=True)

            print("REQUESTING:", next_page, flush=True)
            # exit()

            # --------------------------------------------------
            # REQUEST NEXT PAGE
            # --------------------------------------------------

            yield scrapy.Request(
                url=next_page,
                headers=self.headers,
                callback=self.parse,
                meta={
                    "cat_id": cat_id,
                    "category_name": category_name,
                    "category_url": category_url,
                    "currentversion": currentversion,
                    "site_id": site_id,
                    "site_code": site_code,
                    "usdequal": usdequal,
                    "category_table": category_table,
                    "handle_httpstatus_all": True,
                    "product_count": product_count,
                },
                dont_filter=True,
            )

        # --------------------------------------------------
        # NO MORE PAGES
        # --------------------------------------------------

        else:

            print("NO MORE PAGES", flush=True)

            print("CRAWLING FINISHED", flush=True)

            # --------------------------------------------------
            # GET CATEGORY DATA
            # --------------------------------------------------

            cat_id = response.meta["cat_id"]
            category_url = response.meta["category_url"]
            category_table = response.meta["category_table"]
            currentversion = response.meta["currentversion"]
            product_count = response.meta["product_count"]
            site_code = response.meta["site_code"]

            print("FINAL PRODUCT COUNT:", product_count, flush=True)

            # --------------------------------------------------
            # SEND CATEGORY DATA TO PIPELINE
            # --------------------------------------------------

            item = CategoryDetailsItem()

            item["cat_id"] = cat_id
            item["category_url"] = category_url
            item["category_table"] = category_table
            item["currentversion"] = currentversion
            item["product_count"] = product_count
            item["site_code"] = site_code

            print("######## CATEGORY UPDATE ITEM ########", flush=True)
            print("CAT ID:", cat_id, flush=True)
            print("CATEGORY URL:", category_url, flush=True)
            print("CATEGORY TABLE:", category_table, flush=True)
            print("CURRENT VERSION:", currentversion, flush=True)
            print("PRODUCT COUNT:", product_count, flush=True)

            yield item

        # item = archivedetails()

        # item["currentversion"] = currentversion
        # item["site_code"] = site_code

        # print("######## CATEGORY UPDATE ITEM ########", flush=True)
        # print("Site Code:", site_code, flush=True)
        # print("CURRENT VERSION:", currentversion, flush=True)

        # yield item

    def product_parse(self, response):
        print("###############PRODUCT_PARSE#####################")
        print("product_url:", response.url)
        product_url = response.url

        print("\n======================================")
        print("PPCURRENT PAGE:", response.url)
        print("STATUS:", response.status)
        # print("STATUS:", response.text)
        print("======================================")

        cat_id = response.meta["cat_id"]
        category_name = response.meta["category_name"]
        category_url = response.meta["category_url"]
        currentversion = response.meta["currentversion"]
        site_id = response.meta["site_id"]
        site_code = response.meta["site_code"]
        usdequal = response.meta["usdequal"]
        category_table = response.meta["category_table"]
        print("########################################page")
        # exit()

        json_ld_list = response.css('script[type="application/ld+json"]::text').getall()

        for json_text in json_ld_list:
            try:
                data = json.loads(json_text)

                # Process only Product JSON
                if data.get("@type") != "Product":
                    continue

                # Title
                title = data.get("name")

                # SKU / Product ID
                product_id = data.get("sku")

                # Images
                images = data.get("image", [])

                if isinstance(images, str):
                    images = [images]

                image = images[0] if images else None

                # Multi images
                multiimages = " | ".join(images) if images else None

                # Brand
                brand_data = data.get("brand", {})
                brand = brand_data.get("name") if isinstance(brand_data, dict) else None

                # Offers
                offers = data.get("offers", {})

                if isinstance(offers, dict):
                    price = offers.get("price")
                    product_url = offers.get("url")
                else:
                    price = None
                    product_url = data.get("url")

                availability = data.get("offers", {}).get("availability", "")
                is_available = 1 if "InStock" in availability else 0

                # Rating
                aggregate_rating = data.get("aggregateRating", {})

                if isinstance(aggregate_rating, dict):
                    rating = aggregate_rating.get("ratingValue")
                    noof_rating = aggregate_rating.get("ratingCount")
                else:
                    rating = None
                    noof_rating = None

                # Description
                description = data.get("description")

                # Ingredients
                # Not available in this Product JSON-LD
                ingredients = None
                description_container = response.css(
                    "div.desktop-product-details.markdown noscript div.p-3"
                )

                # Description
                description = " ".join(
                    description_container.css("h2::text, p::text, li::text").getall()
                ).strip()

                # Ingredients
                ingredients = description_container.xpath(
                    ".//p[b[contains(text(), 'Ingredients:')]]/following-sibling::p[1]/text()"
                ).get()

                if ingredients:
                    ingredients = ingredients.strip()

                # Quantity / Size
                # Not available in this Product JSON-LD
                size = None

                # print("TITLE:", title)
                # print("PRICE:", price)
                # print("URL:", product_url)
                # print("IMAGE:", image)
                # print("SKU:", product_id)
                # print("BRAND:", brand)
                # print("RATING:", rating)
                # print("TOTAL RATINGS:", noof_rating)
                # print("DESCRIPTION:", description)
                # print("INGREDIENTS:", ingredients)
                # print("MULTI IMAGES:", multiimages)
                # print("SIZE:", size)
                # print("-" * 80)

                item = ProductItem()

                item["title"] = title
                item["price"] = price
                item["link"] = product_url
                item["image"] = image
                item["sku"] = product_id
                item["brand"] = brand
                item["rating"] = rating
                item["product_rating"] = rating
                item["product_total_ratings"] = noof_rating
                item["description"] = description
                item["ingredients"] = ingredients
                item["multiimages"] = multiimages
                item["qty"] = size
                item["cat_id"] = cat_id
                item["category_name"] = category_name
                item["category_url"] = category_url
                item["currentversion"] = currentversion
                item["site_id"] = site_id
                item["site_code"] = site_code
                item["usdequal"] = usdequal
                item["category_table"] = category_table
                item["is_available"] = is_available

                yield item

            except json.JSONDecodeError:
                continue
