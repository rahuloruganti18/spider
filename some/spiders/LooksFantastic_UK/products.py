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

    print("######## EXAMPLE BBWIT FILE LOADED ########")

    name = "LOOKSUK_prod"

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
        site_id = 940
        site = get_site_config(site_id)
        site_code = site["site_code"]
        category_table = site["category_table"]
        archive_table = site["archive_table"]
        # archive_table = f"{site_code}_Products_Archive"
        print(category_table)
        print(archive_table)
        # exit()
        max_vsel = f"SELECT TOP 2 RecordDate, Version FROM {archive_table} WITH (NOLOCK) ORDER BY RecordDate DESC"

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

        # Find products on current page
        products = response.css("div#product-list .relative aspect-square w-full")
        products = response.css("#product-list product-card-wrapper")
        # print(products)
        # exit()

        product_count = response.meta.get("product_count", 0)

        # Add current page count
        product_count += len(products)
        print("TOTAL PRODUCTS:", len(products))
        # exit()

        count = 0
        for product in products:

            title = product.css("a.product-item::attr(data-title)").get()

            if not title:
                title = product.css("a.product-item-title::text").get()

            if title:
                title = title.strip()

            # --------------------------------------------------
            # Product link
            # --------------------------------------------------

            link = product.css("a.product-item::attr(href)").get()

            if not link:
                link = product.css("a.product-item-title::attr(href)").get()

            if link:
                link = response.urljoin(link)

            # --------------------------------------------------
            # Product price
            # --------------------------------------------------
            price = product.css("p.price span.text-gray-900::text").get()

            # If current price was not found, get the normal price
            if not price:
                price = product.css("p.price > span:not(.sr-only)::text").get()

            if price:
                price = price.strip().replace("£", "").strip()

            # print("PRICE:", price, flush=True)

            # price = product.css("p.product-item-price span.text-gray-900::text").get()
            #
            # if price:
            # price = price.strip()

            # --------------------------------------------------
            # Product image
            # --------------------------------------------------

            image = product.css("img.first-image::attr(src)").get()

            if not image:
                image = product.css("img::attr(src)").get()

            if not image:
                image = product.css("img::attr(data-src)").get()

            if image:
                image = response.urljoin(image)

            # --------------------------------------------------
            # Product SKU
            # --------------------------------------------------

            sku = product.attrib.get("data-quicklook")

            if not sku:
                sku = product.attrib.get("data-quicklook-default-variant")

            if not sku:
                sku = product.attrib.get("data-quicklook-single-variant-sku")

            count += 1
            print("COUNT :", count)
            print("TITLE :", title)
            print("LINK  :", link)
            print("PRICE :", price)
            print("IMG   :", image)
            print("SKU   :", sku)
            print("--------------------------------")
            # exit()

            # Later you can yield this to pipeline/database
            item = ProductItem()

            item["title"] = title
            item["price"] = price
            item["link"] = link
            item["image"] = image
            item["sku"] = sku

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

        product_count = response.css("span.total-products::text").get()

        if product_count:
            product_count = product_count.strip()

        product_count = int(product_count) if product_count else 0

        print("TOTAL PRODUCTS:", product_count, flush=True)

        # --------------------------------------------------
        # PAGINATION
        # --------------------------------------------------

        from urllib.parse import (
            urlparse,
            parse_qs,
            urlencode,
            urlunparse,
        )

        current_page = int(
            parse_qs(urlparse(response.url).query).get("pageNumber", ["1"])[0]
        )

        print("CURRENT PAGE:", current_page, flush=True)
        # --------------------------------------------------
        # GET CURRENT URL
        # --------------------------------------------------

        page_text = response.css("p[aria-label^='Page']::attr(aria-label)").get()

        print("PAGE TEXT:", page_text, flush=True)

        last_page = 1

        if page_text:
            match = re.search(r"Page\s+\d+\s+of\s+(\d+)", page_text)

            if match:
                last_page = int(match.group(1))

        print("LAST PAGE:", last_page, flush=True)

        if current_page < last_page:

            next_page_number = current_page + 1

            parsed_url = urlparse(response.url)
            query = parse_qs(parsed_url.query)

            query["pageNumber"] = [str(next_page_number)]

            next_page = urlunparse(
                (
                    parsed_url.scheme,
                    parsed_url.netloc,
                    parsed_url.path,
                    parsed_url.params,
                    urlencode(query, doseq=True),
                    parsed_url.fragment,
                )
            )

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
