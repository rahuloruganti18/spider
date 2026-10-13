import scrapy
import sys
import json
from urllib.parse import urljoin

from ...items import CategoryItem


class LOOKSUKCategoriesSpider(scrapy.Spider):

    name = "ANIMAL_cat"

    allowed_domains = ["https://www.sams.com.mx/"]

    start_urls = ["https://www.sams.com.mx/"]

    # ------------------------------------------------------
    # SITE DETAILS
    # ------------------------------------------------------

    # site_id = 1
    site_code = "SAMSMX"
    category_table = "SAMSMX_Categories"

    # ------------------------------------------------------
    # PARSE
    # ------------------------------------------------------

    def parse(self, response):

        print()
        print("############################################")
        print("SAMS CATEGORY SPIDER")
        print("############################################")
        print("STATUS:", response.status)
        print("URL:", response.url)
        print()

        # ==================================================
        # GET DEPARTMENTS JSON
        # ==================================================

        script = response.xpath(
            '//script[@id="__NEXT_DATA__" and @type="application/json"]/text()'
        ).get()

        departments = []

        if script:
            try:
                data = json.loads(script)

                modules = (
                    data.get("props", {})
                    .get("pageProps", {})
                    .get("bootstrapData", {})
                    .get("header", {})
                    .get("data", {})
                    .get("contentLayout", {})
                    .get("modules", [])
                )

                if len(modules) > 1:
                    departments = modules[1].get("configs", {}).get("departments", [])

            except json.JSONDecodeError:
                pass

        print("TOTAL DEPARTMENTS:", len(departments), flush=True)
        # exit()

        # for department in departments:
        #     print("NAME:", department.get("name"), flush=True)
        #     print("HEADING:", department.get("heading"), flush=True)
        # exit()

        # ==================================================
        # LOOP MAIN CATEGORIES
        # ==================================================

        categories = []

        seen_categories = set()

        for department in departments:

            # --------------------------------------------------
            # MAIN CATEGORY
            # --------------------------------------------------

            main_name = department.get("name")

            if not main_name:
                continue

            main_name = main_name.strip()

            # Duplicate check
            key = main_name.lower()

            if key in seen_categories:
                continue

            seen_categories.add(key)

            print()
            print("============================================")
            print("MAIN CATEGORY")
            print("============================================")
            print("NAME:", main_name)
            print("PARENT ID: 1")

            # ==================================================
            # SUB CATEGORIES
            # ==================================================

            subcategories = []

            sub_categories = department.get("subCategoryGroup", [])

            print("SUB CATEGORY COUNT:", len(sub_categories), flush=True)

            seen_subcategories = set()

            for sub_category in sub_categories:

                sub_name = sub_category.get("subCategoryHeading")

                if not sub_name:
                    continue

                sub_name = sub_name.strip()

                # Duplicate check
                sub_key = sub_name.lower()

                if sub_key in seen_subcategories:
                    continue

                seen_subcategories.add(sub_key)

                print()
                print("  ------------------------------------------")
                print("  SUB CATEGORY")
                print("  NAME:", sub_name)

                # ==================================================
                # SUB-SUB CATEGORIES
                # ==================================================

                sub_subcategories = []

                sub_sub_links = sub_category.get("subCategoryLinksGroup", [])

                seen_sub_subcategories = set()

                for link_group in sub_sub_links:

                    sub_link = link_group.get("subCategoryLink", {})

                    sub_sub_name = sub_link.get("title")

                    click_through = sub_link.get("clickThrough", {})

                    sub_sub_url = click_through.get("value")

                    if not sub_sub_name:
                        continue

                    if not sub_sub_url:
                        continue

                    if sub_sub_url:
                        sub_sub_url = response.urljoin(sub_sub_url)

                    sub_sub_name = sub_sub_name.strip()

                    # --------------------------------------------------
                    # DUPLICATE CHECK
                    # --------------------------------------------------

                    sub_sub_key = (sub_sub_name.lower(), sub_sub_url)

                    if sub_sub_key in seen_sub_subcategories:
                        continue

                    seen_sub_subcategories.add(sub_sub_key)

                    print("    SUB-SUB CATEGORY:", sub_sub_name, flush=True)

                    print("    URL:", sub_sub_url, flush=True)

                    # --------------------------------------------------
                    # ADD SUB-SUB CATEGORY
                    # --------------------------------------------------

                    sub_subcategories.append(
                        {
                            "sub_sub_category_name": sub_sub_name,
                            "sub_sub_category_url": sub_sub_url,
                            "sub_sub_category_level": 3,
                        }
                    )

                # ==================================================
                # ADD SUB CATEGORY
                # ==================================================

                subcategories.append(
                    {
                        "sub_category_name": sub_name,
                        "sub_category_url": None,
                        "sub_category_level": 2,
                        "sub_subcategories": sub_subcategories,
                    }
                )

            # ==================================================
            # SEND MAIN CATEGORY TO PIPELINE
            # ==================================================

            # categories.append(
            #     {
            #         "category_name": main_name,
            #         "category_url": None,
            #         "category_level": 1,
            #         "subcategories": subcategories,
            #     }
            # )

            print()
            print("SENDING CATEGORY TO PIPELINE:", main_name, flush=True)
            # print(subcategories)
            # exit()

            yield CategoryItem(
                category_name=main_name,
                category_url=None,
                parent_id=1,
                category_table=self.category_table,
                category_level=1,
                subcategories=subcategories,
            )
