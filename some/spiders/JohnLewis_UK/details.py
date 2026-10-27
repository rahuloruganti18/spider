import scrapy
import json
import sys
import re
from ...items import ProductDetailsItem
from ...database.db import get_connection


class JOHNUKDetailsSpider(scrapy.Spider):

    name = "john_details"

    allowed_domains = ["https://www.johnlewis.com"]

    currentversion = 2
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

    async def start(self):

        print()
        print("############################################")
        print("######## JOHNUK DETAILS SPIDER START ########")
        print("############################################")

        # -----------------------------------------
        # DATABASE CONNECTION
        # -----------------------------------------

        self.connection = get_connection()
        self.cursor = self.connection.cursor()
        site_code = "JOHNUK"
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

            yield scrapy.Request(
                url=product_url,
                headers=self.headers,
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
        description = response.css(
            # 'div[data-testid="description:content"] ::text'
            "div.ProductDescriptionSideDrawer_descriptionContainer__mpNPy ::text"
        ).getall()

        description = " ".join(text.strip() for text in description if text.strip())

        # print("DESCRIPTION:", description, flush=True)

        print("DESCRIPTION:", description, flush=True)

        # MULTIPLE PRODUCT IMAGES

        image_urls = response.css(
            'button[data-testid^="grid\\:gallery\\:image\\:wrapper"] img::attr(src)'
        ).getall()

        multiimages = []

        for image_url in image_urls:

            if image_url.startswith("//"):
                image_url = "https:" + image_url

            # Remove HTML query parameters
            image_url = image_url.split("?")[0]

            if image_url not in multiimages:
                multiimages.append(image_url)

        multiimage_url = " | ".join(multiimages)

        print("MULTIIMAGES:", multiimage_url, flush=True)
        # exit()

        yield ProductDetailsItem(
            product_id=product_id,
            description=description,
            multiimage_url=multiimage_url,
            product_table=product_table,
            site_code=site_code,
            currentversion=currentversion,
        )

    def closed(self, reason):

        print()
        print("############################################")
        print("######## JOHNUK DETAILS SPIDER CLOSED #######")
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
