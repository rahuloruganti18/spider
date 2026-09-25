import scrapy
from ...items import ProductItem, CategoryDetailsItem
import sys
import pyodbc
import json
import re

from ...database.db import get_connection
from ...database.site_config import get_site_config
from ...database.site_config import get_conversion_rate


class ExampleSpider(scrapy.Spider):

    print("######## EXAMPLE BBWIT FILE LOADED ########")

    name = "breu_prod"
    domain = "https://www.breuninger.com/de/"

    async def start(self):

        print("######## START REQUESTS ########", flush=True)

        connection = get_connection()
        cursor = connection.cursor()

        site_id = 960
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
        sql = f"SELECT SubCategoryID,SubCategoryName,SubCategoryURL,CurrentVersion FROM {category_table} WITH (NOLOCK) WHERE SubCategoryID NOT IN (SELECT ParentCategoryID FROM {category_table} WHERE ParentCategoryID IS NOT NULL) AND PriceICCategoryID IS NOT NULL ORDER BY SubCategoryID"

        cursor.execute(sql)
        rows = cursor.fetchall()
        print("TOTAL CATEGORY URLS:", len(rows))
        # exit()

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
        print("CURRENT PAGE:", response.url)
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

        products = response.css(
            "ul.navi-productlist__content li.navi-productlist__item--product"
        )

        print("PRODUCT COUNT:", len(products), flush=True)

        for product in products:

            # ============================================================
            # PRODUCT NAME
            # ============================================================

            title_text = product.css(
                "span[data-test-navi-product-name-text]::text"
            ).get()

            title_additional = product.css(
                "span[data-test-navi-product-name-additional]::text"
            ).get()

            title_parts = []

            if title_text:
                title_parts.append(title_text.strip())

            if title_additional:
                title_parts.append(title_additional.strip())

            title = " ".join(title_parts)

            # ============================================================
            # PRODUCT LINK
            # ============================================================

            link = product.css("a[data-product-link]::attr(href)").get()

            if link:
                link = response.urljoin(link)

            # ============================================================
            # PRICE
            # ============================================================

            price = product.css("div[data-test-navi-product-current-price]::text").get()
            if not price:
                price = product.css("span[data-test-ents-sale-price]::text").get()

            if price:
                price = price.replace("\xa0", " ").strip()
                price = price.replace("€", "").strip()
                price = price.replace(",", ".")
                price = price.replace("ab", "").strip()

                try:
                    price = float(price)
                except ValueError:
                    price = None

            # ============================================================
            # SKU
            # ============================================================

            sku = product.css("navi-product::attr(data-syan)").get()

            if sku:
                sku = sku.strip()

            # ============================================================
            # IMAGE
            # ============================================================

            image = product.css("img[data-test-navi-product-image]::attr(src)").get()

            if image:
                image = response.urljoin(image)

            # ============================================================
            # BRAND
            # ============================================================

            brand = product.css("span[data-test-navi-product-brand]::text").get()

            if brand:
                brand = brand.strip()

            # ============================================================
            # UNIT / BASE PRICE
            # ============================================================

            unitprice = product.css(
                "div[data-test-navi-product-base-price]::text"
            ).get()

            if unitprice:
                unitprice = unitprice.replace("\xa0", " ").strip()
                unitprice = unitprice.strip("()").strip()

            # ============================================================
            # SIZE / qty
            # ============================================================

            qty = product.css("a[data-navi-product-article]::attr(data-sizes)").get()

            if qty:
                qty = qty.strip()
                if qty.startswith("[") and qty.endswith("]"):
                    qty = qty.strip("[]").strip()
                    qty = qty.strip("'\"").strip()

            # ============================================================
            # PRINT
            # ============================================================

            print("TITLE:", title, flush=True)
            print("LINK:", link, flush=True)
            print("PRICE:", price, flush=True)
            print("SKU:", sku, flush=True)
            print("IMAGE:", image, flush=True)
            print("brand:", brand, flush=True)
            print("unitprice:", unitprice, flush=True)
            print("qty:", qty, flush=True)
            print("----------------------------------------", flush=True)
            # exit()

            # Later you can yield this to pipeline/database
            item = ProductItem()

            item["title"] = title
            item["price"] = price
            item["link"] = link
            item["img"] = image
            item["sku"] = sku
            item["brand"] = brand
            item["unitprice"] = unitprice
            item["qty"] = qty

            item["cat_id"] = response.meta["cat_id"]
            item["category_name"] = response.meta["category_name"]
            item["category_url"] = response.meta["category_url"]
            item["currentversion"] = response.meta["currentversion"]
            item["site_id"] = response.meta["site_id"]
            item["site_code"] = response.meta["site_code"]
            item["usdequal"] = response.meta["usdequal"]
            item["category_table"] = response.meta["category_table"]

            # print("######## ABOUT TO YIELD ########")
            # print(dict(item))

            yield item

            # PRODUCT COUNT

        # --------------------------------------------------
        # TOTAL PRODUCTS
        # --------------------------------------------------
        print("######## ALL PRODUCTS FINISHED ########", flush=True)

        # --------------------------------------------------
        # FINAL PRODUCT COUNT
        # --------------------------------------------------
        product_count = response.css(
            "div[data-test-navi-productlist-load-more-progress] span.navi-productlist__load-more__progress__numbers::text"
        ).getall()

        if product_count and len(product_count) >= 2:
            product_count = product_count[1].strip()
        else:
            product_count = None

        print("PRODUCT COUNT:", product_count, flush=True)

        # NEXT PAGE
        # next_page = response.css("li.pages-item-next a.action.next::attr(href)").get()
        next_page = response.css(
            "navi-productlist[data-test-navi-productlist]::attr(data-next-page-url)"
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
