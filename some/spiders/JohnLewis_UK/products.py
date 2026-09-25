import scrapy
from ...items import ProductItem
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

    name = "john_prod"
    domain = "https://www.johnlewis.com"

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "max-age=0",
        "cookie": "mt.v=5.1179692659.1789737326248; jl_uuid=aaf1c487-f853-41d0-bea4-1c79b7537ea2; ib=a93a651848862cff5ad81ca0cdc7ea0d; ens_session_count=1; ens_session=1; ravelinDeviceId=rjs-d40c9918-69ef-4d06-9d42-9f5c25f085a3; ravelinSessionId=rjs-d40c9918-69ef-4d06-9d42-9f5c25f085a3:4c5a6b8b-bea4-4800-ade9-74d26c67631c; uuid=e51dc411-7915-4b90-b61d-d68951d39d24; JOHNLEWIS_ENSIGHTEN_PRIVACY_BANNER_VIEWED=1; JOHNLEWIS_ENSIGHTEN_PRIVACY_Advertising=0; JOHNLEWIS_ENSIGHTEN_PRIVACY_Analytics=0; JOHNLEWIS_ENSIGHTEN_PRIVACY_Essentials=1; JOHNLEWIS_ENSIGHTEN_PRIVACY_Functional=0; JOHNLEWIS_ENSIGHTEN_PRIVACY_Personalisation=0; bm_mi=AEB075FDC4180EE293E717887203ABE2~YAAQTZUjF5yOJLKgAQAAIH+otAE/3uniUDW45SQiWpunInACaZWd/amQYIlATos6+Lean/ltXwJ0HproYhX9Fvddx+Yg4WNRx+zfWgto54roLolh9iFv3AY0SDVg70DBX6Yg5S5kvbzy2BI8f69WFJoj+kR92Jrlll5RliOIEN4mV/26z7jO8YeDtXp4Q3GiDMuORTSzoskEn5+cOFvAZhzBe7hsy2jwCoj7K/4/5dlZPQeNcTkDOj513PTqeZgiRxSziP0hutMvYo/VMdgEL7NDbEvHYEHB4grswtFCvAOnjIPXsrT5Wi6FjCRvo2h9A4V2bAxZYLymblE4AW8KQ30YLyDb25FOJo5ygRJZl5ICyUYB+3BcpS8=~1; ensnav=tf%7Cbeauty%7Cfragrance%7Cwomen's%20perfume; bm_sz=D257252A7E9BD8F9CA0B7E1D9DC3CE11~YAAQTZUjFzKPJLKgAQAAYomotAHRBKYqQPYWcNacel6H55RjJH9bnJ9tlV8+iA4ACUvQyWHH3PjFar3LziYRAUaQaT3g2Nz8JbcwXTF+SmRQPNeisRaChBr64KMyNYVPoPTATCNBPOowgB4ys+9neCpl+PKYhjvC7rA845B3mebLhcm0mh9h+dTHiZu+GapPxoyUuhQeRly/w8YDc1a23fMFT+H9CuB5oILueCM+2z+PICke3I3/JQ/YhCfoCFB8inmWSwPsozmi7EEWPs8TMq2GPt+hf8o5AiLzlioll0EarZZCSgvDSERoNPclZyf65+q+3T/LaNXcXIRYOncgaVmg/TIdFMmDkBIpcIZuMjvWPixAMaSNffFSVOuieKWimw19yeAHJn1v9SyQ80QUuJXxjMQE0+ALk9IeR4pO589Xh50M~3291447~3552048; _abck=2CBC3EEF1272FCE1EE05E0FA6FAFF7D0~0~YAAQTZUjFzqPJLKgAQAAHoqotBDiBpWOwkRRG7dT+2ds6kI942e6rVRUn5JVEycswPjL0kgpp3Wmk5M3VpJHmAFU6ueHv2GwqQ5XQYsRNSoQ3ULeLPrNmTIdBU2Pi/0SfqJEzqZrjIGZTepeITt0si+7NeXXVCgz9uH1vVn61sjLs69qSKq/oCEmvrvwEBq7HzvCLN8HyScDIh1WLAIYFpoSBEiSFY3/bVJZGVysX7Z43mg9dnZ4ynlsodLIE1vTnO/Zpm9k5itPh12byY49VhdwvQey71kdKaQXiHMqv0GPpVGzL6xMhEaMvRFlY+WdlcGc8Uc8g+48vxxs8fu1sCO05v1MeG4x42Oa4ImcvoeZUpKJmyd1Shu1Wf1P2LsJm17r576D69yq7fEOEGWJjtHG30TMWFybzLFdISC8Gk+PyShoH5iL13PpkRvLqJtWpmZQKoPlsvBqq+SQyY4bbeGaa3kJaMqjWUNLgPrMnLLj/0QhIb6IOxRJjagB4ijAu+HaJBgX+eOwRWFypcA5vhcmoLVtSWKXulJaN+8no29Mf9hOU0C+v2X1jx99z2D8oOlBHkjcFGXFuJ4QNGIuj+O8J7OEJaIhG/JttPfZgHcLVN2JNvRVQk0e13BYFWP4frhVxp3OlfRvx3iWoEfBIOkmFwkG7/P3KFVU9A==~-1~-1~-1~AAQAAAAG%2f%2f%2f%2f%2fwaOIYwLKtr%2fcuFmsV5cL3tFDCSEYImRJTBJdNoKFGKnakisDxnB8yakj+0csbRiF7L+5IuHrRaIxEaRCQl+bK%2fKYhcYQYq9iuQA~-1; ens_current_session_id=1789737340178; ensAppData=%7B%22prevPage%22%3A%22jl%3Abeauty%3Awomen's%20fragrance%3Agrid%22%7D; ak_bmsc=CD61FBB3B266CF6D3200582265863B99~000000000000000000000000000000~YAAQTZUjF36PJLKgAQAAAY6otAHa6+VE4qMJNhVYP/k4iV3MW183Mb/YfWpoWiZ4yi+eU4Xk++GR8UgLbbalT5TlO7kYGk9lfMzI//dke5sZZdaKDQp6+0CQWy0X8y1x7bNnAzhimyBCLEqCnuddrjst5hYZmm+p9WffTyv/RW1WR8MvihutGlCHQ3Aj31jVCG46RdsvywH0CC78H5uISxjwWpLh6aYZ0NU0hhBkHO8WCAPo6lVvvlE0FcDdiki1vEVw4xXJkQO6EgFSm9sKI3v13KYq0n7j24iKBokfQzDc2AY3Jv3ha86ba/nVl4aP7bDapywiR+y0EwEawaHWOC5tlatnyJxCDdFK+y4q42pIAKpwZI/ehL8pWHMQrI7GukVPnOGJRaxPysBmUQVTh8rb54XI79QfwzpDj2DhfN/e3NVS2aXrRp0x9VpkscjF+M5g19t+ALJ6YrVo9G/KAc9KbNzVoejwyjVSq1LEghs6V7tC98XhV2Sz2d2RHVKuzZ8fE0QBIgHVstC/Ccng0hcsRlw0EooAI60cZ+0=; jlpwlg=eyJraW5kIjoiTElTVCIsInRva2VuIjoidTBkYWhnWDgyMzNjNTUwNjI1MmY0NWE4OGU2ZjViY2M5ODAzYjQ0ZSIsImhhc2giOiJiN2Y5Nzg4NjgxYzgwZmE2ZjM0NzllMDU1NzI0YjI4NjQxOGZmNjRjMTVjOTIxOGE1ZjliZGZmMGZjYTRjMDJlYjIzYzEyNzAxNGVmMzdmYWU5OWIyMmMyNmJlYmZjMDE3M2YzMTUwZDlkYzg1MDU3MTkwYmM2ZDIyNDRmMWM2NiIsInZlcnNpb24iOjF9; bm_sv=E3CAD031914955C8E09E7AEB3AD93B9E~YAAQTZUjF7SQJLKgAQAA8aiotAHdclrO1deVfRDP2GbVEVqwgErSz3xGzBzHKUYs1BnJIVujghyP/mxRoO3qSKANLma0Sf6xUiUNKvolcvvm/quRTzvgJ9diybtQ2l3RnnfOvMy4jXRJPbha2Pyu4L1ajpj9wdU5XbRQwsXyGpe+XLRwontZGQfwtlbCkxffyaItnD+dzCm8//GCNZZ2tSUmWnstKlHTSFf16DbXJrDbZm8+H+ajxb78yI/xrEOVX8/WBMUksZzJokU=~1",
        "if-none-match": 'W/"1r7qssf5h3giq4"',
        "priority": "u=0, i",
        "referer": "https://www.johnlewis.com/",
        "sec-ch-ua": '"Chromium";v="152", "Not?A_Brand";v="24", "Google Chrome";v="152"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36",
    }

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
        site_id = 946
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

        next_data = response.css("script#__NEXT_DATA__::text").get()

        if not next_data:
            print("NEXT_DATA NOT FOUND", flush=True)
            return

        data = json.loads(next_data)

        product_data = (
            data.get("props", {}).get("pageProps", {}).get("productListingData", {})
        )

        prod_count = product_data.get("results", 0)

        products = product_data.get("products", [])

        print("PRODUCT COUNT:", prod_count, flush=True)
        # next_page = response.css('a[data-testid="next-btn"]::attr(href)').get()

        # if next_page:
        #     next_page = response.urljoin(next_page)

        # print(next_page)
        # exit()

        for product in products:
            # print(product)
            # exit()

            title = product.get("title")

            link = product.get("url")

            if link:
                link = response.urljoin(link)

            price = product.get("variantPriceRange", {}).get("value", {}).get("min")

            sku = product.get("defaultSkuId")

            image = product.get("image")

            if image and image.startswith("//"):
                image = "https:" + image

            # Multi images
            multiimages = []

            if image:
                multiimages.append(image)

            for alt_image in product.get("alternativeImageUrls", []):

                if alt_image.startswith("//"):
                    alt_image = "https:" + alt_image

                # Remove alt1, alt2, alt3...
                alt_image = re.sub(r"alt\d+(?=\??$)", "", alt_image)

                if alt_image not in multiimages:
                    multiimages.append(alt_image)

            multiimages = " | ".join(multiimages)

            # Rating
            rating = product.get("averageRating")

            ProductRating = product.get("averageRating")

            ProductTotalRatings = product.get("reviews")

            # Brand
            brand = product.get("brand")

            # Volume
            volume = None

            for attribute in product.get("attributes", []):

                if attribute.get("key") == "volume":
                    values = attribute.get("values", [])

                    if values:
                        volume = ", ".join(values)

                    break

            # Availability from colorSwatches
            is_available = 0

            color_swatches = product.get("colorSwatches", [])

            if color_swatches:
                is_available = (
                    1
                    if any(
                        swatch.get("isAvailable") is True for swatch in color_swatches
                    )
                    else 0
                )

            # count += 1
            print("================================", flush=True)
            print("TITLE:", title, flush=True)
            print("LINK:", link, flush=True)
            print("PRICE:", price, flush=True)
            print("SKU:", sku, flush=True)
            print("IMAGE:", image, flush=True)
            print("PROD_COUNT:", prod_count, flush=True)
            print("RATING:", rating, flush=True)
            print("ProductRating:", ProductRating, flush=True)
            print("ProductTotalRatings:", ProductTotalRatings, flush=True)
            print("MULTIIMAGES:", multiimages, flush=True)
            print("BRAND:", brand, flush=True)
            print("VOLUME:", volume, flush=True)
            print("IS_AVAILABLE:", is_available, flush=True)
            # exit()

            # Later you can yield this to pipeline/database
            item = ProductItem()

            item["title"] = title
            item["price"] = price
            item["link"] = link
            item["img"] = image
            item["sku"] = sku
            item["prod_count"] = prod_count
            item["rating"] = rating
            item["ProductRating"] = ProductRating
            item["ProductTotalRatings"] = ProductTotalRatings
            item["multiimages"] = multiimages
            item["brand"] = brand
            item["volume"] = volume
            item["is_available"] = is_available

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

        # PRODUCT COUNT
        product_count = response.css('div[data-testid="total-items"]::text').getall()

        product_count = "".join(product_count).strip()

        # print("PRODUCT COUNT TEXT:", prod_count_text, flush=True)

        match = re.search(r"of\s+(\d+)", product_count)

        if match:
            product_count = int(match.group(1))
        else:
            product_count = 0

        print("TOTAL PRODUCT COUNT:", prod_count, flush=True)

        # NEXT PAGE
        next_page = response.css('a[data-testid="next-btn"]::attr(href)').get()

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
