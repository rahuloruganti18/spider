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

    print("######## EXAMPLE ANIMAL FILE LOADED ########")

    name = "allure_prod"
    # allowed_domains = ["https://allure.com.ng/"]
    # start_urls = ["https://allure.com.ng/"]

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.site_id = 1018
        site = get_site_config(self.site_id)

        self.site_code = site["site_code"]
        self.category_table = site["category_table"]
        self.archive_table = site["archive_table"]

        print("SITE CODE:", self.site_code, flush=True)

    async def start(self):
        print("######## START REQUESTS ########", flush=True)

        connection = get_connection()
        cursor = connection.cursor()

        site_id = self.site_id
        site_code = self.site_code
        category_table = self.category_table
        archive_table = self.archive_table
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
        # sql = f"SELECT SubCategoryID,SubCategoryName,SubCategoryURL,CurrentVersion FROM COSMELK_Categories WITH (NOLOCK) WHERE SubCategoryID=2"

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
                # headers=self.headers,
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

        product_elements = response.xpath(
            ".//li[contains(@class, 'product type-product')]"
        )

        product_urls = []

        for product in product_elements:
            url = product.xpath(".//a/@href").get()
            if url:
                product_urls.append(response.urljoin(url))

        # print("PRODUCT URLS:", product_urls, flush=True)
        print("TOTAL PRODUCTS:", len(product_urls), flush=True)
        # exit()

        # ============================================================
        # CREATE REQUESTS
        # ============================================================

        for url in product_urls:

            if url.startswith("/"):
                url = response.urljoin(url)

            yield scrapy.Request(
                url=url,
                # headers=self.headers,
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

        product_count_text = response.xpath(
            "//div[contains(@class, 'woocommerce-result-count')]//span/text()"
        ).get()

        match = (
            re.search(r"\bof\s+(\d+)\s+results\b", product_count_text)
            if product_count_text
            else None
        )

        product_count = int(match.group(1)) if match else 0

        print("TOTAL PRODUCTS:", product_count, flush=True)

        next_page = response.xpath('//link[@rel="next"]/@href').get()

        print("NEXT PAGE:", next_page, flush=True)

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
                # headers=self.headers,
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

        # Extract JSON-LD structured data
        json_ld_scripts = response.css(
            'script[type="application/ld+json"]::text'
        ).getall()

        for script in json_ld_scripts:
            try:
                data = json.loads(script)
            except json.JSONDecodeError:
                continue

            # Handle JSON-LD objects and @graph structures
            objects = (
                data.get("@graph", [])
                if isinstance(data, dict) and "@graph" in data
                else (data if isinstance(data, list) else [data])
            )

            for obj in objects:
                if not isinstance(obj, dict):
                    continue

                obj_type = obj.get("@type", [])

                if isinstance(obj_type, str):
                    obj_type = [obj_type]

                if "Product" not in obj_type:
                    continue

                # Product details
                title = obj.get("name")
                product_id = obj.get("sku")

                brand_data = obj.get("brand", {})
                if isinstance(brand_data, dict):
                    brand = brand_data.get("name")
                else:
                    brand = brand_data

                description = obj.get("description")

                # Product image
                images = obj.get("image", [])

                if isinstance(images, str):
                    image = images
                elif isinstance(images, list) and images:
                    first_image = images[0]
                    if isinstance(first_image, dict):
                        image = first_image.get("url")
                    else:
                        image = first_image

                # Price and availability
                offers = obj.get("offers", {})

                if isinstance(offers, list):
                    offers = offers[0] if offers else {}

                if isinstance(offers, dict):
                    price = offers.get("price")
                    product_url = offers.get("url", response.url)

                    availability = offers.get("availability", "")
                    is_available = availability.rstrip("/").endswith("InStock")

                # Extract rating and number of ratings
                aggregate_rating = obj.get("aggregateRating", {})

                if isinstance(aggregate_rating, dict):
                    rating = aggregate_rating.get("ratingValue")
                    noof_rating = aggregate_rating.get(
                        "ratingCount"
                    ) or aggregate_rating.get("reviewCount")
                else:
                    rating = None
                    noof_rating = None
                print("TITLE:", title)
                print("PRICE:", price)
                print("URL:", product_url)
                print("IMAGE:", image)
                # print("SKU:", variant)
                print("SKU:", product_id)
                print("BRAND:", brand)
                print("RATING:", rating)
                print("TOTAL RATINGS:", noof_rating)
                print("DESCRIPTION:", description)
                print("IS_AVAILABLE:", is_available)
                # print("MULTI IMAGES:", multiimages)
                print("-" * 80)
                # exit()

                item = ProductItem()

                item["title"] = title
                item["price"] = price
                item["link"] = product_url
                item["image"] = image
                # item["variant"] = variant
                item["sku"] = product_id
                item["brand"] = brand
                item["rating"] = rating
                item["product_rating"] = rating
                item["product_total_ratings"] = noof_rating
                item["description"] = description
                item["cat_id"] = cat_id
                item["category_name"] = category_name
                item["category_url"] = category_url
                item["currentversion"] = currentversion
                item["site_id"] = site_id
                item["site_code"] = site_code
                item["usdequal"] = usdequal
                item["category_table"] = category_table
                item["is_available"] = is_available
                # item["multiimages"] = multiimages

                yield item
                break
