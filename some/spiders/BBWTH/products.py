import scrapy
from ...items import ProductItem
import sys
import pyodbc

# from ...database import site_config
from ...database.db import get_connection
from ...database.site_config import get_site_config
from ...database.site_config import get_conversion_rate


class ExampleSpider(scrapy.Spider):

    print("######## EXAMPLE BBWTH FILE LOADED ########")

    name = "bbwth_proucts"

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
        site_id = 910
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
        print("======================================")

        cat_id = response.meta["cat_id"]
        category_name = response.meta["category_name"]
        category_url = response.meta["category_url"]
        currentversion = response.meta["currentversion"]
        site_id = response.meta["site_id"]
        site_code = response.meta["site_code"]
        usdequal = response.meta["usdequal"]
        category_table = response.meta["category_table"]
        print(
            "#################################################################################################################page"
        )

        # Find products on current page
        products = response.css("div.product")
        # print(products)
        # exit()

        product_count = response.meta.get("product_count", 0)

        # Add current page count
        product_count += len(products)
        print("TOTAL PRODUCTS:", len(products))
        # exit()

        count = 0
        for product in products:

            # title = product.css("p.b-product-tile__name::text").get()
            product_name = product.css("p.js-product-tile-name::text").get()
            product_type = product.css("p.product-type::text").get()

            product_name = product_name.strip() if product_name else ""
            product_type = product_type.strip() if product_type else ""

            title = f"{product_name} {product_type}".strip()
            link = product.css("a.b-product-tile__link::attr(href)").get()
            # price = product.css("span.value::attr(content)").get()
            price = product.css("span.promo-price::text").get()

            if price:
                # Promo price is the main/current price
                price = price.strip()
            else:
                # No promo price, use normal price
                price = product.css("span.value::attr(content)").get()

            if price:
                price = price.replace("THB", "").strip()
            img = product.css("img.b-product-tile__img::attr(data-src)").get()
            sku = product.attrib.get("data-pid")

            if link:
                link = response.urljoin(link)

            if img:
                img = response.urljoin(img)

            count += 1
            print("COUNT :", count)
            print("TITLE :", title)
            print("LINK  :", link)
            print("PRICE :", price)
            print("IMG   :", img)
            print("SKU   :", sku)
            print("--------------------------------")
            # exit()

            # Later you can yield this to pipeline/database
            item = ProductItem()

            item["title"] = title
            item["price"] = price
            item["link"] = link
            item["img"] = img
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

        current_page = response.css("a.pagination-link.active::text").get()
        current_page = current_page.strip() if current_page else "1"
        current_page = int(current_page)
        print("CURRENT PAGE NUMBER:", current_page)

        page_links = response.css("a.pagination-link::attr(href)").getall()
        print("TOTAL PAGE LINKS:", len(page_links))
        next_page = None
        for href in page_links:

            page_number = response.urljoin(href)
            if f"page={current_page + 1}" in page_number:
                next_page = page_number
                break

        print("NEXT PAGE:", next_page)

        if next_page:

            print("REQUESTING:", next_page)

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

        else:

            print("NO MORE PAGES")
            print("CRAWLING FINISHED")
            cat_id = response.meta["cat_id"]
            category_url = response.meta["category_url"]

            print("FINAL PRODUCT COUNT:", product_count)

            connection = get_connection()
            cursor = connection.cursor()
            category_table = response.meta["category_table"]
            sql = f"UPDATE {category_table} SET CurrentVersion= ?, ActualProductCount = ? WHERE SubCategoryURL = ?"
            values = (currentversion, product_count, category_url)
            print(f"SQL QUERY:{sql}")
            print("VALUES:", values)
            cursor.execute(sql, values)
            # cursor.execute(f"UPDATE BBWAU_Categories SET ProductCount = ? WHERE SubCategoryID = ?", (product_count, cat_id))
            connection.commit()
            cursor.close()
            connection.close()
            print(f"CATEGORY {cat_id} UPDATED: " f"{product_count} PRODUCTS")
