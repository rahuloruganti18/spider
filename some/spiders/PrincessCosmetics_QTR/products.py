import scrapy
from ...items import ProductItem, CategoryDetailsItem
import pyodbc
import json
import datetime
import os
import re

from ...database.db import get_connection
from ...database.site_config import get_site_config
from ...database.site_config import get_conversion_rate


class ExampleSpider(scrapy.Spider):

    print("######## EXAMPLE PRINCESSCOSMETICS FILE LOADED ########")

    name = "princessqtr_prod"
    # allowed_domains = ["https://princesscosmeticsqa.com/"]
    # start_urls = ["https://princesscosmeticsqa.com/"]

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.site_id = 1094
        site = get_site_config(self.site_id)

        self.site_code = site["site_code"]
        self.category_table = site["category_table"]
        self.products_table = site["products_table"]
        self.archive_table = site["archive_table"]

        print("SITE CODE:", self.site_code, flush=True)
        now = datetime.datetime.now()
        log_date = now.strftime("%Y-%m-%d")

        if self.site_code:

            log_dir = rf"C:\Logs\{self.site_code}"

            os.makedirs(log_dir, exist_ok=True)

            self.log_file_path = os.path.join(
                log_dir, f"product_update_errors_{log_date}.log"
            )

            # print("SITE CODE:", self.site_code, flush=True)
            print("LOG FILE:", self.log_file_path, flush=True)

        else:
            now = datetime.datetime.now()
            log_date = now.strftime("%Y-%m-%d")
            log_dir = r"C:\Logs\{site_code}"
            os.makedirs(log_dir, exist_ok=True)

            self.log_file_path = os.path.join(
                log_dir, f"product_update_errors_{log_date}.log"
            )

    async def start(self):
        print("######## START REQUESTS ########", flush=True)

        connection = get_connection()
        cursor = connection.cursor()

        site_id = self.site_id
        site_code = self.site_code
        category_table = self.category_table
        products_table = self.products_table
        archive_table = self.archive_table
        print(category_table)
        print(products_table)
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

        usdequal = get_conversion_rate(site_code)
        sql = f"SELECT SubCategoryID,SubCategoryName,SubCategoryURL,CurrentVersion FROM {category_table} WITH (NOLOCK) WHERE SubCategoryID NOT IN (SELECT ParentCategoryID FROM {category_table} WHERE ParentCategoryID IS NOT NULL) AND PriceICCategoryID IS NOT NULL AND SubCategoryName NOT LIKE '%all%' ORDER BY SubCategoryID"

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

        cat_id = response.meta["cat_id"]
        category_name = response.meta["category_name"]
        category_url = response.meta["category_url"]
        currentversion = response.meta["currentversion"]
        site_id = response.meta["site_id"]
        site_code = response.meta["site_code"]
        usdequal = response.meta["usdequal"]
        category_table = response.meta["category_table"]
        product_count = ""
        print("########################################parse_page")
        connection = get_connection()
        cursor = connection.cursor()
        products_table = self.products_table

        try:
            product_elements = response.xpath('.//div[@class="product-card__wrapper"]')

            product_urls = []

            for product in product_elements:
                url = product.xpath(".//a/@href").get()
                # if url:
                #     product_urls.append(response.urljoin(url))

                if not url:
                    continue

                url = response.urljoin(url)
                print("PRODUCT URL:", url)
                # exit()

                cursor.execute(
                    f"""SELECT productid, description,Version FROM {products_table} WHERE ProductURL = ?""",
                    (url,),
                )

                product_record = cursor.fetchone()
                if product_record and product_record[2] == currentversion:
                    now = datetime.datetime.now()
                    error_time = now.strftime("%Y-%m-%d %H:%M:%S")
                    error_message = (
                        f"[{error_time}] "
                        f"PRODUCT RECORD IS SAME VERSION - ProductId : {product_record[0]} - ProductVersion : {product_record[2]}"
                    )
                    with open(self.log_file_path, "a", encoding="utf-8") as log_file:

                        log_file.write(error_message + "\n")
                    continue

                if (
                    product_record
                    and product_record[0]
                    and product_record[1]
                    and product_record[1].strip()
                ):
                    # Existing product with a non-empty description.
                    # Pass the existing listing-page product element.
                    print("Calling existing product function")

                    now = datetime.datetime.now()
                    error_time = now.strftime("%Y-%m-%d %H:%M:%S")
                    error_message = (
                        f"[{error_time}] "
                        f"Calling existing product function - ProductID : {product_record[0]} - ProductVersion : {product_record[2]}"
                    )
                    with open(self.log_file_path, "a", encoding="utf-8") as log_file:

                        log_file.write(error_message + "\n")
                    # exit()
                    yield from self.existing_product(
                        response=response,
                        product=product,
                        productid=product_record[0],
                        url=url,
                    )
                else:
                    # Missing product or empty description
                    product_urls.append(url)
        finally:
            cursor.close()
            connection.close()

        # print("PRODUCT URLS:", product_urls, flush=True)
        print("PRODUCTS URLS:", len(product_urls), flush=True)
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

        product_count = response.xpath(
            "//div[@class='collection-product-count']/text()"
        ).re_first(r"(\d+)")

        product_count = int(product_count) if product_count else 0

        print("TOTAL PRODUCTS:", product_count, flush=True)

        next_page = response.xpath('//link[@rel="next"]/@href').get()

        # print("NEXT PAGE:", next_page, flush=True)
        # exit()

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
            # exit()

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

    def product_parse(self, response):
        print("###############PRODUCT_PARSE#####################")
        print("product_url:", response.url)
        product_url = response.url

        print("\n======================================")
        print("PPCURRENT PAGE:", response.url)
        print("STATUS:", response.status)
        # print("STATUS:", response.text)
        print("======================================")

        title = product_url = image = product_id = description = brand = offers = (
            price
        ) = availability = is_available = ProductCodeName = ProductCodevalue = (
            was_price
        ) = rating = noof_rating = None

        cat_id = response.meta["cat_id"]
        category_name = response.meta["category_name"]
        category_url = response.meta["category_url"]
        currentversion = response.meta["currentversion"]
        site_id = response.meta["site_id"]
        site_code = response.meta["site_code"]
        usdequal = response.meta["usdequal"]
        category_table = response.meta["category_table"]
        print("########################################Product_parse_page")
        # exit()

        multiimages = response.xpath(
            '//div[contains(@class,"f-product__media") and @data-media-type="image"]/@data-src'
        ).getall()

        multiimages = "|".join(
            dict.fromkeys(
                img if img.startswith("http") else "https:" + img for img in multiimages
            )
        )

        # Get all JSON-LD scripts
        scripts = response.xpath(
            '//script[@type="application/ld+json"]/text()'
        ).getall()

        data = {}

        # Find Product or ProductGroup
        for script in scripts:
            try:
                obj = json.loads(script)

                objects = obj if isinstance(obj, list) else [obj]

                for d in objects:
                    if not isinstance(d, dict):
                        continue

                    schema = d.get("@type", "")

                    if isinstance(schema, list):
                        schema = next(
                            (s for s in schema if s in ["Product", "ProductGroup"]), ""
                        )

                    if schema in ["Product", "ProductGroup"]:
                        data = d
                        break

                if data:
                    break

            except (json.JSONDecodeError, TypeError):
                continue

        if not data:
            return

        schema_type = data.get("@type", "")

        # Common product details
        title = data.get("name", "")

        brand_data = data.get("brand", {})
        brand = (
            brand_data.get("name", "") if isinstance(brand_data, dict) else brand_data
        )

        description = data.get("description", "")
        category_name = data.get("category", "")
        product_url = data.get("url", response.url)

        # Check ProductGroup or Product
        if schema_type == "ProductGroup":
            variants = data.get("hasVariant", [])
        else:
            variants = [data]

        # Extract all images
        all_images = []

        if schema_type == "ProductGroup":
            for v in variants:
                img = v.get("image", [])
                if isinstance(img, list):
                    all_images.extend(img)
                elif img:
                    all_images.append(img)
        else:
            img = data.get("image", [])
            if isinstance(img, list):
                all_images.extend(img)
            elif img:
                all_images.append(img)

        # multiimages = "|".join(dict.fromkeys(all_images))

        # Yield each product / variant
        for variant in variants:

            offers = variant.get("offers", {})

            price = offers.get("price", "")

            if isinstance(offers, list):
                offers = offers[0] if offers else {}

            if not isinstance(offers, dict):
                offers = {}

            product_id = (
                variant.get("sku")
                or variant.get("gtin")
                or variant.get("productID")
                or data.get("productGroupID", "")
            )

            image = variant.get("image", "")

            if isinstance(image, list):
                image = image[0] if image else ""

            availability = offers.get("availability", "")
            is_available = 1 if "InStock" in availability else 2

            ProductCodeName = "gtin"
            ProductCodevalue = product_id

            print("TITLE:", title)
            print("PRICE:", price)
            print("URL:", product_url)
            print("IMAGE:", image)
            print("was_price:", was_price)
            print("SKU:", product_id)
            print("ProductCodeName:", ProductCodeName)
            print("ProductCodevalue:", ProductCodevalue)
            print("BRAND:", brand)
            print("RATING:", rating)
            print("TOTAL RATINGS:", noof_rating)
            print("DESCRIPTION:", description)
            print("IS_AVAILABLE:", is_available)
            print("MULTI IMAGES:", multiimages)
            print("-" * 80)
            # exit()

            item = ProductItem()

            item["title"] = title
            item["price"] = price
            item["link"] = product_url
            item["image"] = image
            item["was_price"] = was_price
            item["sku"] = product_id
            item["ProductCodeName"] = ProductCodeName
            item["ProductCodevalue"] = ProductCodevalue
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
            item["multiimages"] = multiimages

            yield item

    def existing_product(self, response, product, productid, url):

        print("\n======================================")
        print("PPCURRENT PAGE:", response.url)
        print("STATUS:", response.status)
        # print("STATUS:", response.text)
        print("PRODUCT:", product)
        print("Product ID:", productid)
        print("Product URL:", url)
        print("======================================")
        # exit()
        title = product_url = image = product_id = price = was_price = None

        cat_id = response.meta["cat_id"]
        category_name = response.meta["category_name"]
        category_url = response.meta["category_url"]
        currentversion = response.meta["currentversion"]
        site_id = response.meta["site_id"]
        site_code = response.meta["site_code"]
        usdequal = response.meta["usdequal"]
        category_table = response.meta["category_table"]
        print("########################################existing_product_page")
        print("Pending this code")
        exit()
        # Product title
        title = product.xpath(
            "normalize-space(.//a[contains(@class, 'tqln-card__name')]/text())"
        ).get()

        # Product URL
        product_url = product.xpath(
            ".//a[contains(@class, 'tqln-card__name')]/@href"
        ).get()

        product_url = response.urljoin(product_url) if product_url else url

        # Main product image
        image = product.xpath(
            ".//a[contains(@class, 'tqln-card__img')]//img/@src"
        ).get()

        if image:
            image = response.urljoin(image)

        # Product ID
        data_id = product.xpath("./@data-id").get()

        # Product SKU
        product_id = product.xpath(
            ".//button[contains(@class, 'add_to_cart_button')]/@data-product_sku"
        ).get()

        # Sale price / displayed price
        price = product.xpath(
            "normalize-space(.//span[contains(@class, 'tqln-card__price')]//bdi)"
        ).get()
        if price:
            price = float(price.replace("OMR", "").strip().replace(",", "."))

        was_price = product.xpath(
            "normalize-space(.//span[contains(@class, 'tqln-card__old')]//bdi)"
        ).get()
        if was_price:
            was_price = float(price.replace("OMR", "").strip().replace(",", "."))
        # Rating
        rating = product.xpath(
            ".//span[contains(@class, 'tqln-card__rate')]/@aria-label"
        ).get()

        print("TITLE:", title)
        print("PRICE:", price)
        print("URL:", product_url)
        print("IMAGE:", image)
        print("was_price:", was_price)
        print("SKU:", product_id)
        print("cat_id:", cat_id)
        print("category_name:", category_name)
        print("category_url:", category_url)
        print("currentversion:", currentversion)
        print("site_id:", site_id)
        print("site_code:", site_code)
        print("usdequal:", usdequal)
        print("category_table:", category_table)
        exit()

        item = ProductItem()

        item["title"] = title
        item["price"] = price
        item["link"] = product_url
        item["image"] = image
        item["was_price"] = was_price
        item["sku"] = product_id
        item["cat_id"] = cat_id
        item["category_name"] = category_name
        item["category_url"] = category_url
        item["currentversion"] = currentversion
        item["site_id"] = site_id
        item["site_code"] = site_code
        item["usdequal"] = usdequal
        item["category_table"] = category_table

        yield item
