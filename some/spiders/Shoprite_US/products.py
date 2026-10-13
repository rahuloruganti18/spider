import scrapy
from ...items import ProductItem
import sys
import pyodbc
import re

# from ...database import site_config
from ...database.db import get_connection
from ...database.site_config import get_site_config
from ...database.site_config import get_conversion_rate


class ExampleSpider(scrapy.Spider):

    print("######## EXAMPLE SHOPRITE FILE LOADED ########")

    name = "shoprite_prod"

    # start_urls = ["https://www.bathandbodyworks.com.au/body-care"]
    async def start(self):
        """print("######## START REQUESTS ########", flush=True)

        yield scrapy.Request(
            url="https://www.bathandbodyworks.com.au/body-care",
            callback=self.parse
        )"""

        print("######## START REQUESTS ########")

        connection = get_connection()
        cursor = connection.cursor()
        """site_config.load_site_config()

        print(site_config.SITE_ID)
        print(site_config.SITE_CODE)
        print(site_config.CATEGORY_TABLE)
        print(site_config.PRODUCT_TABLE)
        print(site_config.ARCHIVE_TABLE)
        site_id = site_config.SITE_ID
        site_code = site_config.SITE_CODE
        category_table = site_config.CATEGORY_TABLE
        archive_table = site_config.ARCHIVE_TABLE"""
        site_id = 947
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
            print("######## BEFORE PRODUCT REQUEST ########", flush=True)
            print("CATEGORY URL:", category_url, flush=True)
            print("CAT ID:", cat_id, flush=True)
            print("CATEGORY NAME:", category_name, flush=True)
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
            print("######## REQUEST CREATED ########", flush=True)

        # exit()

        cursor.close()
        connection.close()

    def parse(self, response):

        print("\n======================================")
        print("CURRENT PAGE:", response.url)
        print("STATUS:", response.status)
        # print("STATUS:", response.text)
        print("======================================")
        if response.status == 403:
            print("######## SHOPRITE RETURNED 403 ########", flush=True)

            # If Zyte middleware has not already replaced the response,
            # you can handle the fallback here temporarily for debugging.

            return

        cat_id = response.meta["cat_id"]
        category_name = response.meta["category_name"]
        category_url = response.meta["category_url"]
        currentversion = response.meta["currentversion"]
        site_id = response.meta["site_id"]
        site_code = response.meta["site_code"]
        usdequal = response.meta["usdequal"]
        category_table = response.meta["category_table"]
        print("########################################page")

        product_count = 0

        products = response.css("article[data-testid^='ProductCardWrapper-']")

        # Add current page count
        product_count += len(products)

        print("TOTAL PRODUCTS:", len(products), flush=True)
        # exit()

        count = 0

        for product in products:

            title = product.css("h3 button::text").get()
            title = title.strip() if title else None

            link = product.css('a[class*="ProductCardHiddenLink"]::attr(href)').get()
            if link:
                link = response.urljoin(link)

            price = product.css('div[class*="ProductPrice"]::text').get()
            price = price.replace("$", "").strip() if price else None

            sku = product.attrib.get("data-testid", "").replace(
                "ProductCardWrapper-", ""
            )

            img = product.css(
                'div[data-testid*="productCardImage"] img::attr(src)'
            ).get()

            unitprice = product.css('div[class*="ProductUnitPrice"]::text').get()
            if unitprice:
                unitprice = unitprice.replace("$", "").strip()
            else:
                unitprice = None

            was_price = product.css(
                'div[data-testid="ProductCardWasPrice-testid"] div::text'
            ).re_first(r"was\s*\$?([\d.]+)")
            if was_price:
                was_price = was_price.replace("$", "").strip()
            else:
                was_price = None
            unitprice = unitprice.strip() if unitprice else None
            was_price = was_price.strip() if was_price else None

            # qty = product.css('div[data-testid^="promotionBadge-"]::text').re_first(
            #     r"Limit\s+(\d+)"
            # )
            # qty = qty.strip() if qty else None
            count += 1
            print("TITLE:", title, flush=True)
            print("PRICE:", price, flush=True)
            print("UNIT PRICE:", unitprice, flush=True)
            print("WAS PRICE:", was_price, flush=True)
            # print("QTY:", qty, flush=True)
            print("SKU:", sku, flush=True)
            print("IMAGE:", img, flush=True)
            print("LINK:", link, flush=True)
            # exit()

            # Later you can yield this to pipeline/database
            item = ProductItem()

            item["title"] = title
            item["link"] = link
            item["price"] = price
            item["sku"] = sku
            item["img"] = img
            item["unitprice"] = unitprice
            item["was_price"] = was_price

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

        print("######## ALL PRODUCTS FINISHED ########", flush=True)

        # --------------------------------------------------
        # TOTAL PRODUCTS
        # --------------------------------------------------
        print("######## CHECKING PAGINATION ########", flush=True)

        next_page = response.css('link[rel="next"]::attr(href)').get()
        print(next_page)

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

            # --------------------------------------------------
            # FINAL PRODUCT COUNT
            # --------------------------------------------------

            print("FINAL PRODUCT COUNT:", product_count, flush=True)

            # --------------------------------------------------
            # DATABASE CONNECTION
            # --------------------------------------------------

            connection = get_connection()

            cursor = connection.cursor()

            # --------------------------------------------------
            # UPDATE CATEGORY
            # --------------------------------------------------

            sql = f"""
                UPDATE {category_table}
                SET
                    CurrentVersion = ?,
                    ActualProductCount = ?
                WHERE SubCategoryURL = ?
            """

            values = (
                currentversion,
                product_count,
                category_url,
            )

            print("SQL QUERY:", sql, flush=True)

            print("VALUES:", values, flush=True)

            # --------------------------------------------------
            # EXECUTE UPDATE
            # --------------------------------------------------

            cursor.execute(sql, values)

            connection.commit()

            # --------------------------------------------------
            # CLOSE DATABASE
            # --------------------------------------------------

            cursor.close()

            connection.close()

            print(
                f"CATEGORY {cat_id} UPDATED: " f"{product_count} PRODUCTS", flush=True
            )
