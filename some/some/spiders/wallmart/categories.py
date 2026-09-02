import scrapy

from urllib.parse import urljoin

from ...database.db import zyte
from ...items import CategoryItem


class WalmartCatSpider(scrapy.Spider):

    name = "walmart_cat"

    allowed_domains = ["walmart.com"]

    start_urls = ["https://www.walmart.com/all-departments"]

    # ==========================================================
    # START
    # ==========================================================

    async def start(self):

        print("######## WALMART CAT STARTED ########", flush=True)

        site_code = "WALMART1"
        site_id = 5

        # Main category parent is always 1
        parent_id = 1

        category_table = f"{site_code}_Categories"

        for url in self.start_urls:

            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={
                    "site_id": site_id,
                    "site_code": site_code,
                    "category_table": category_table,
                    "parent_id": parent_id,
                },
                dont_filter=True,
            )

    # ==========================================================
    # MAIN CATEGORY PAGE
    # ==========================================================

    def parse(self, response):

        print()
        print("######## WALMART CAT PARSE ########", flush=True)

        site_id = response.meta["site_id"]
        site_code = response.meta["site_code"]
        category_table = response.meta["category_table"]

        # Main category parent = 1
        parent_id = response.meta["parent_id"]

        print("STATUS:", response.status, flush=True)

        print("URL:", response.url, flush=True)

        # ======================================================
        # CHECK WALMART RESPONSE
        # ======================================================

        body_start = response.body[:5000].decode("utf-8", errors="ignore").lower()

        print("RESPONSE LENGTH:", len(response.body), flush=True)

        rejected = False

        if "request rejected" in body_start:

            rejected = True

        elif "your support id is" in body_start:

            rejected = True

        # ======================================================
        # CALL ZYTE IF WALMART REJECTED
        # ======================================================

        if rejected:

            print("######## WALMART RESPONSE REJECTED ########", flush=True)

            print("######## CALLING ZYTE ########", flush=True)

            zyte_response = zyte(response.url)

            if not zyte_response:

                print("######## ZYTE RETURNED EMPTY ########", flush=True)

                return

            print("######## ZYTE RESPONSE RECEIVED ########", flush=True)

            from scrapy.http import TextResponse

            response = TextResponse(
                url=response.url, body=zyte_response, encoding="utf-8"
            )

        # ======================================================
        # FINAL RESPONSE
        # ======================================================

        print("######## FINAL WALMART RESPONSE ########", flush=True)

        print("STATUS:", response.status, flush=True)

        # ======================================================
        # FIND MAIN CATEGORY BLOCKS
        #
        # Example:
        #
        # <h2>
        #    Grocery
        # </h2>
        #
        # <ul>
        #    <li>
        #       <a>Food</a>
        #    </li>
        # </ul>
        #
        # h2 = MAIN CATEGORY
        # li a = SUB CATEGORY
        # ======================================================

        category_blocks = response.xpath(
            "//div["
            'contains(concat(" ", normalize-space(@class), " "), " ld_BD ") '
            "and "
            'contains(concat(" ", normalize-space(@class), " "), " ld_CC ") '
            "and .//h2[1]/a[1] "
            "and .//ul[1]/li/a[1]"
            "]"
        )

        print("CATEGORY BLOCKS:", len(category_blocks), flush=True)

        seen_categories = set()

        # ======================================================
        # MAIN CATEGORY LOOP
        # ======================================================

        for block in category_blocks:

            # ==================================================
            # MAIN CATEGORY NAME
            # ==================================================

            category_name = block.xpath("normalize-space(.//h2[1]/a[1])").get()

            # ==================================================
            # MAIN CATEGORY URL
            # ==================================================

            category_url = block.xpath(".//h2[1]/a[1]/@href").get()

            if not category_name:
                continue

            if not category_url:
                continue

            category_name = category_name.strip()

            category_url = urljoin(response.url, category_url.strip())

            # ==================================================
            # MAIN CATEGORY DUPLICATE CHECK
            # ==================================================

            category_key = (category_name.lower(), category_url)

            if category_key in seen_categories:
                continue

            seen_categories.add(category_key)

            print()
            print("==========================================", flush=True)

            print("MAIN CATEGORY:", category_name, flush=True)

            print("MAIN URL:", category_url, flush=True)

            print("MAIN PARENT ID:", parent_id, flush=True)

            print("==========================================", flush=True)

            # ==================================================
            # GET SUB CATEGORIES FROM THIS MAIN CATEGORY BLOCK
            #
            # IMPORTANT:
            #
            # These are ONLY collected here.
            #
            # They are NOT inserted here.
            #
            # Pipeline will:
            #
            # 1. Insert main
            # 2. Get main ID
            # 3. Insert sub using main ID
            # 4. Get sub ID
            # 5. Open sub URL
            # ==================================================

            sub_links = block.xpath(".//ul[1]/li/a[@href]")

            print("SUB CATEGORY COUNT:", len(sub_links), flush=True)

            seen_subcategories = set()

            subcategories = []

            # ==================================================
            # SUB CATEGORY LOOP
            # ==================================================

            for sub_link in sub_links:

                sub_name = sub_link.xpath("normalize-space(.)").get()

                sub_url = sub_link.xpath("./@href").get()

                if not sub_name:
                    continue

                if not sub_url:
                    continue

                sub_name = sub_name.strip()

                sub_url = urljoin(response.url, sub_url.strip())

                # ==================================================
                # SUB CATEGORY DUPLICATE CHECK
                # ==================================================

                sub_key = (sub_name.lower(), sub_url)

                if sub_key in seen_subcategories:
                    continue

                seen_subcategories.add(sub_key)

                print()
                print("------------------------------------------", flush=True)

                print("SUB CATEGORY:", sub_name, flush=True)

                print("SUB URL:", sub_url, flush=True)

                print("SUB PARENT WILL BE MAIN ID", flush=True)

                print("------------------------------------------", flush=True)

                subcategories.append({"name": sub_name, "url": sub_url})

            # ==================================================
            # SEND MAIN CATEGORY + SUB CATEGORY INFORMATION
            # TO PIPELINE
            # ==================================================

            item = CategoryItem()

            item["category_name"] = category_name
            item["category_url"] = category_url

            item["site_id"] = site_id
            item["site_code"] = site_code
            item["category_table"] = category_table

            # MAIN CATEGORY PARENT = 1
            item["parent_id"] = 1

            # Pipeline uses these to insert sub categories
            item["subcategories"] = subcategories

            print()
            print("######## YIELDING MAIN CATEGORY TO PIPELINE ########", flush=True)

            print("MAIN CATEGORY:", category_name, flush=True)

            print("SUB CATEGORY COUNT:", len(subcategories), flush=True)

            yield item

    # ==========================================================
    # CREATE REQUEST FOR SUB CATEGORY PAGE
    # ==========================================================

    def make_subcategory_request(
        self,
        url,
        sub_category_name,
        sub_category_url,
        sub_category_id,
        site_id,
        site_code,
        category_table,
    ):

        print()
        print("######## CREATING SUB CATEGORY REQUEST ########", flush=True)

        print("SUB CATEGORY:", sub_category_name, flush=True)

        print("SUB URL:", sub_category_url, flush=True)

        print("SUB CATEGORY ID:", sub_category_id, flush=True)

        return scrapy.Request(
            url=url,
            callback=self.parse_subcategory,
            meta={
                "sub_category_name": sub_category_name,
                "sub_category_url": sub_category_url,
                # IMPORTANT:
                #
                # This ID becomes ParentCategoryID
                # for the sub-sub categories.
                #
                "sub_category_id": sub_category_id,
                "site_id": site_id,
                "site_code": site_code,
                "category_table": category_table,
            },
            dont_filter=True,
        )

    # ==========================================================
    # SUB CATEGORY PAGE
    #
    # Example:
    #
    # Grocery
    #    |
    #    └── Pantry
    #          |
    #          └── Weekly Essentials
    #
    # Here Pantry ID is used as parent ID
    # for Weekly Essentials.
    # ==========================================================

    # def parse_subcategory(self, response):

    #     print()
    #     print("######## WALMART SUB CATEGORY PAGE ########", flush=True)

    #     print("STATUS:", response.status, flush=True)

    #     print("URL:", response.url, flush=True)

    #     sub_category_name = response.meta["sub_category_name"]

    #     sub_category_id = response.meta["sub_category_id"]

    #     site_id = response.meta["site_id"]

    #     site_code = response.meta["site_code"]

    #     category_table = response.meta["category_table"]

    #     print("SUB CATEGORY:", sub_category_name, flush=True)

    #     print("SUB CATEGORY ID:", sub_category_id, flush=True)

    #     # ======================================================
    #     # CHECK WALMART REJECTION
    #     # ======================================================

    #     body_start = response.body[:5000].decode("utf-8", errors="ignore").lower()

    #     rejected = False

    #     if "request rejected" in body_start:

    #         rejected = True

    #     elif "your support id is" in body_start:

    #         rejected = True

    #     # ======================================================
    #     # ZYTE
    #     # ======================================================

    #     if rejected:

    #         print("######## SUB CATEGORY RESPONSE REJECTED ########", flush=True)

    #         print("######## CALLING ZYTE ########", flush=True)

    #         zyte_response = zyte(response.url)

    #         if not zyte_response:

    #             print("######## ZYTE RETURNED EMPTY ########", flush=True)

    #             return

    #         print("######## ZYTE RESPONSE RECEIVED ########", flush=True)

    #         from scrapy.http import TextResponse

    #         response = TextResponse(
    #             url=response.url, body=zyte_response, encoding="utf-8"
    #         )

    #     # ======================================================
    #     # FIND "SHOP BY CATEGORY"
    #     #
    #     # This is where Walmart has the final
    #     # sub-sub categories.
    #     # ======================================================

    #     shop_by_category_sections = response.xpath(
    #         "//section["
    #         ".//h2["
    #         "contains("
    #         "translate("
    #         "normalize-space(.),"
    #         "'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
    #         "'abcdefghijklmnopqrstuvwxyz'"
    #         "),"
    #         "'shop by category'"
    #         ")"
    #         "]"
    #         "]"
    #     )

    #     print()
    #     print("SHOP BY CATEGORY SECTIONS:", len(shop_by_category_sections), flush=True)

    #     if not shop_by_category_sections:

    #         print("######## NO SUB-SUB CATEGORY FOUND ########", flush=True)

    #         return

    #     # ======================================================
    #     # SUB-SUB CATEGORY LOOP
    #     # ======================================================

    #     seen_sub_subcategories = set()

    #     for section in shop_by_category_sections:

    #         links = section.xpath('.//*[@role="listitem"]//a[@href]')

    #         print("SUB-SUB CATEGORY LINKS:", len(links), flush=True)

    #         for link in links:

    #             sub_sub_name = link.xpath("normalize-space(.//span[1])").get()

    #             if not sub_sub_name:

    #                 sub_sub_name = link.xpath("normalize-space(.)").get()

    #             sub_sub_url = link.xpath("./@href").get()

    #             if not sub_sub_name:
    #                 continue

    #             if not sub_sub_url:
    #                 continue

    #             sub_sub_name = sub_sub_name.strip()

    #             sub_sub_url = urljoin(response.url, sub_sub_url.strip())

    #             # ==================================================
    #             # DUPLICATE CHECK
    #             # ==================================================

    #             sub_sub_key = (sub_sub_name.lower(), sub_sub_url)

    #             if sub_sub_key in seen_sub_subcategories:
    #                 continue

    #             seen_sub_subcategories.add(sub_sub_key)

    #             print()
    #             print("==========================================", flush=True)

    #             print("SUB-SUB CATEGORY:", sub_sub_name, flush=True)

    #             print("SUB-SUB URL:", sub_sub_url, flush=True)

    #             print("SUB-SUB PARENT ID:", sub_category_id, flush=True)

    #             print("==========================================", flush=True)

    #             # ==================================================
    #             # SEND SUB-SUB CATEGORY TO PIPELINE
    #             # ==================================================

    #             item = CategoryItem()

    #             item["category_name"] = sub_sub_name
    #             item["category_url"] = sub_sub_url

    #             item["site_id"] = site_id
    #             item["site_code"] = site_code
    #             item["category_table"] = category_table

    #             # IMPORTANT:
    #             #
    #             # Parent is the SUB CATEGORY ID.
    #             #
    #             item["parent_id"] = sub_category_id

    #             # No further children at this level
    #             item["subcategories"] = []

    #             print("######## YIELDING SUB-SUB TO PIPELINE ########", flush=True)

    #             yield item

    def parse_subcategory(self, response):

        print()
        print("######## WALMART SUB CATEGORY PAGE ########", flush=True)

        print("STATUS:", response.status, flush=True)
        print("URL:", response.url, flush=True)

        sub_category_name = response.meta["sub_category_name"]
        sub_category_id = response.meta["sub_category_id"]

        site_id = response.meta["site_id"]
        site_code = response.meta["site_code"]
        category_table = response.meta["category_table"]

        print("SUB CATEGORY:", sub_category_name, flush=True)
        print("SUB CATEGORY ID:", sub_category_id, flush=True)

        # ======================================================
        # CHECK WALMART REJECTION
        # ======================================================

        body_start = response.body[:5000].decode("utf-8", errors="ignore").lower()

        rejected = False

        if "request rejected" in body_start:
            rejected = True

        elif "your support id is" in body_start:
            rejected = True

        # ======================================================
        # ZYTE
        # ======================================================

        if rejected:

            print("######## SUB CATEGORY RESPONSE REJECTED ########", flush=True)

            print("######## CALLING ZYTE ########", flush=True)

            zyte_response = zyte(response.url)

            if not zyte_response:

                print("######## ZYTE RETURNED EMPTY ########", flush=True)

                return

            print("######## ZYTE RESPONSE RECEIVED ########", flush=True)

            from scrapy.http import TextResponse

            response = TextResponse(
                url=response.url, body=zyte_response, encoding="utf-8"
            )

        # ======================================================
        # FINAL RESPONSE
        # ======================================================

        print("######## LOOKING FOR WALMART JSON ########", flush=True)

        text = response.text

        print("RESPONSE LENGTH:", len(text), flush=True)

        # ======================================================
        # JSON
        # ======================================================

        import json
        import re

        sub_subcategories = []

        # ======================================================
        # 1. categories4x1
        # ======================================================

        print("######## SEARCHING categories4x1 ########", flush=True)

        categories4x1_matches = re.findall(
            r'"categories4x1"\s*:\s*(\[[\s\S]*?\])\s*,\s*"publishedDate"', text
        )

        print("categories4x1 MATCHES:", len(categories4x1_matches), flush=True)

        for match in categories4x1_matches:

            try:

                categories4x1 = json.loads(match)

            except Exception as e:

                print("categories4x1 JSON ERROR:", e, flush=True)

                continue

            if not isinstance(categories4x1, list):
                continue

            for category in categories4x1:

                if not isinstance(category, dict):
                    continue

                sub_sub_name = category.get("name")

                image = category.get("image")

                if not isinstance(image, dict):
                    continue

                click_through = image.get("clickThrough")

                if not isinstance(click_through, dict):
                    continue

                sub_sub_url = click_through.get("value")

                if not sub_sub_name:
                    continue

                if not sub_sub_url:
                    continue

                sub_sub_name = sub_sub_name.strip()
                sub_sub_url = urljoin(response.url, sub_sub_url.strip())

                sub_subcategories.append((sub_sub_name, sub_sub_url))

        # ======================================================
        # 2. rows6 -> categories
        # ======================================================

        print("######## SEARCHING rows6 ########", flush=True)

        rows6_matches = re.findall(
            r'"rows6"\s*:\s*(\[[\s\S]*?\])\s*,\s*"publishedDate"', text
        )

        print("rows6 MATCHES:", len(rows6_matches), flush=True)

        for match in rows6_matches:

            try:

                rows6 = json.loads(match)

            except Exception as e:

                print("rows6 JSON ERROR:", e, flush=True)

                continue

            if not isinstance(rows6, list):
                continue

            for row in rows6:

                if not isinstance(row, dict):
                    continue

                categories = row.get("categories")

                if not isinstance(categories, list):
                    continue

                for category in categories:

                    if not isinstance(category, dict):
                        continue

                    sub_sub_name = category.get("name")

                    image = category.get("image")

                    if not isinstance(image, dict):
                        continue

                    click_through = image.get("clickThrough")

                    if not isinstance(click_through, dict):
                        continue

                    sub_sub_url = click_through.get("value")

                    if not sub_sub_name:
                        continue

                    if not sub_sub_url:
                        continue

                    sub_sub_name = sub_sub_name.strip()

                    sub_sub_url = urljoin(response.url, sub_sub_url.strip())

                    sub_subcategories.append((sub_sub_name, sub_sub_url))

        # ======================================================
        # REMOVE DUPLICATES
        # ======================================================

        seen_sub_subcategories = set()

        final_sub_subcategories = []

        for sub_sub_name, sub_sub_url in sub_subcategories:

            key = (sub_sub_name.lower(), sub_sub_url)

            if key in seen_sub_subcategories:
                continue

            seen_sub_subcategories.add(key)

            final_sub_subcategories.append(
                {
                    "name": sub_sub_name,
                    "url": sub_sub_url,
                }
            )

        # ======================================================
        # PRINT RESULT
        # ======================================================

        print()
        print("==========================================", flush=True)

        print("SUB CATEGORY:", sub_category_name, flush=True)

        print("SUB CATEGORY ID:", sub_category_id, flush=True)

        print("SUB-SUB CATEGORY COUNT:", len(final_sub_subcategories), flush=True)

        print("==========================================", flush=True)

        # ======================================================
        # SEND EACH SUB-SUB CATEGORY TO PIPELINE
        # ======================================================

        for sub_sub_category in final_sub_subcategories:

            sub_sub_name = sub_sub_category["name"]
            sub_sub_url = sub_sub_category["url"]

            print()
            print("------------------------------------------", flush=True)

            print("SUB-SUB CATEGORY:", sub_sub_name, flush=True)

            print("SUB-SUB URL:", sub_sub_url, flush=True)

            print("SUB-SUB PARENT ID:", sub_category_id, flush=True)

            print("------------------------------------------", flush=True)

            # ==================================================
            # SEND TO PIPELINE
            # ==================================================

            item = CategoryItem()

            item["category_name"] = sub_sub_name
            item["category_url"] = sub_sub_url

            item["site_id"] = site_id
            item["site_code"] = site_code
            item["category_table"] = category_table

            # VERY IMPORTANT
            # Sub-sub category parent = Sub-category ID
            item["parent_id"] = sub_category_id

            item["subcategories"] = []

            print("######## YIELDING SUB-SUB TO PIPELINE ########", flush=True)

            yield item
