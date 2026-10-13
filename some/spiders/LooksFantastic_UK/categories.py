import scrapy
import sys
from urllib.parse import urljoin

from ...items import CategoryItem


class LOOKSUKCategoriesSpider(scrapy.Spider):

    name = "LOOKSUK_cat"

    allowed_domains = ["lookfantastic.com"]

    start_urls = ["https://www.lookfantastic.com/"]

    # ------------------------------------------------------
    # SITE DETAILS
    # ------------------------------------------------------

    # site_id = 1
    site_code = "LOOKSUK"
    category_table = "LOOKSUK_Categories"

    # ------------------------------------------------------
    # PARSE
    # ------------------------------------------------------

    def parse(self, response):

        print()
        print("############################################")
        print("LOOKSUK CATEGORY SPIDER")
        print("############################################")
        print("STATUS:", response.status)
        print("URL:", response.url)
        print()

        # --------------------------------------------------
        # GET MAIN CATEGORIES
        # --------------------------------------------------

        main_categories = response.xpath('//div[@data-e2e="nav-item"]')

        print("TOTAL MAIN CATEGORIES:", len(main_categories), flush=True)

        # --------------------------------------------------
        # LOOP MAIN CATEGORIES
        # --------------------------------------------------

        for index, main_category in enumerate(main_categories):

            # --------------------------------------------------
            # SKIP FIRST 5 MAIN CATEGORIES
            #
            # Python indexes:
            # 0, 1, 2, 3, 4
            # --------------------------------------------------

            if index < 5:

                print("SKIPPING MAIN CATEGORY INDEX:", index, flush=True)

                continue

            # --------------------------------------------------
            # SKIP INDEX 11
            #
            # This means the 12th main category.
            # --------------------------------------------------

            if index == 11:

                print("SKIPPING MAIN CATEGORY INDEX:", index, flush=True)

                continue

            # --------------------------------------------------
            # GET MAIN CATEGORY LINK
            # --------------------------------------------------

            main_link = main_category.xpath('.//a[@data-e2e="nav-control-item"][1]')

            main_name = main_link.xpath("normalize-space(.//p)").get()

            main_url = main_link.xpath("./@href").get()

            # --------------------------------------------------
            # VALIDATE MAIN CATEGORY
            # --------------------------------------------------

            if not main_name:
                continue

            if not main_url:
                continue

            main_name = main_name.strip()

            main_url = urljoin(response.url, main_url)

            print()
            print("============================================")
            print("MAIN CATEGORY")
            print("============================================")
            print("INDEX:", index)
            print("NAME:", main_name)
            print("URL:", main_url)
            print("PARENT ID: 1")

            # --------------------------------------------------
            # FIND NAVIGATION CONTAINER
            # --------------------------------------------------

            navigation_container = main_category.xpath(
                ".//div[contains("
                'concat(" ", normalize-space(@class), " "), '
                '" navigation-container "'
                ")]"
            )

            # --------------------------------------------------
            # NO NAVIGATION CONTAINER
            # --------------------------------------------------

            if not navigation_container:

                print("NO NAVIGATION CONTAINER:", main_name, flush=True)

                # --------------------------------------------------
                # MAIN CATEGORY PARENT ID IS ALWAYS 1
                # --------------------------------------------------

                yield CategoryItem(
                    category_name=main_name,
                    category_url=main_url,
                    parent_id=1,
                    category_table=self.category_table,
                    # site_id=self.site_id,
                    # site_code=self.site_code,
                    category_level=1,
                    subcategories=[],
                )

                continue

            # --------------------------------------------------
            # GET SUB CATEGORIES
            # --------------------------------------------------

            sub_categories = navigation_container.xpath(
                "./div[contains("
                'concat(" ", normalize-space(@class), " "), '
                '" cols "'
                ")]"
                "/div[contains("
                'concat(" ", normalize-space(@class), " "), '
                '" sub-nav-item "'
                ")]"
            )

            print("SUB CATEGORY COUNT:", len(sub_categories), flush=True)

            # --------------------------------------------------
            # STORE SUB CATEGORIES
            # --------------------------------------------------

            subcategories_data = []

            # --------------------------------------------------
            # DUPLICATE CHECK FOR SUB CATEGORIES
            # --------------------------------------------------

            seen_subcategories = set()

            # --------------------------------------------------
            # LOOP SUB CATEGORIES
            # --------------------------------------------------

            for sub_category in sub_categories:

                # --------------------------------------------------
                # GET SUB CATEGORY LINK
                #
                # Only accept links containing:
                # category-heading
                #
                # This skips headings such as:
                # Trending
                # Top Brands
                # --------------------------------------------------

                """sub_link = sub_category.xpath(
                    "./a[contains("
                    'concat(" ", normalize-space(@class), " "), '
                    '" category-heading "'
                    ")][1]"
                )"""
                sub_link = sub_category.xpath(
                    "./*[self::a or self::div][contains("
                    'concat(" ", normalize-space(@class), " "), '
                    '" category-heading "'
                    ")][1]"
                )

                if not sub_link:
                    continue

                # --------------------------------------------------
                # SUB CATEGORY NAME
                # --------------------------------------------------

                sub_name = sub_link.xpath("normalize-space(.//p)").get()

                # --------------------------------------------------
                # SUB CATEGORY URL
                # --------------------------------------------------

                sub_url = sub_link.xpath("./@href").get()

                # --------------------------------------------------
                # VALIDATE
                # --------------------------------------------------

                if not sub_name:
                    continue

                # if not sub_url:
                # continue

                sub_name = sub_name.strip()

                sub_url = urljoin(response.url, sub_url)

                # --------------------------------------------------
                # DUPLICATE CHECK
                # --------------------------------------------------

                sub_key = (sub_name.lower(), sub_url)

                if sub_key in seen_subcategories:
                    continue

                seen_subcategories.add(sub_key)

                print()
                print("  ------------------------------------------")
                print("  SUB CATEGORY")
                print("  NAME:", sub_name)
                print("  URL:", sub_url)

                # --------------------------------------------------
                # GET SUB-SUB CATEGORY CONTAINERS
                # --------------------------------------------------

                sub_sub_containers = sub_category.xpath(
                    "./div["
                    "contains("
                    'concat(" ", normalize-space(@class), " "), '
                    '" sub-nav-item "'
                    ") "
                    "and "
                    "contains("
                    'concat(" ", normalize-space(@class), " "), '
                    '" py-3 "'
                    ")"
                    "]"
                )

                # --------------------------------------------------
                # STORE SUB-SUB CATEGORIES
                # --------------------------------------------------

                sub_subcategories_data = []

                # --------------------------------------------------
                # DUPLICATE CHECK
                # --------------------------------------------------

                seen_sub_subcategories = set()

                # --------------------------------------------------
                # LOOP SUB-SUB CONTAINERS
                # --------------------------------------------------

                for sub_sub_container in sub_sub_containers:

                    # --------------------------------------------------
                    # GET ALL LINKS
                    # --------------------------------------------------

                    sub_sub_links = sub_sub_container.xpath(".//a[@href]")

                    # --------------------------------------------------
                    # LOOP SUB-SUB LINKS
                    # --------------------------------------------------

                    for sub_sub_link in sub_sub_links:

                        # --------------------------------------------------
                        # SUB-SUB NAME
                        # --------------------------------------------------

                        sub_sub_name = sub_sub_link.xpath("normalize-space(.)").get()

                        # --------------------------------------------------
                        # SUB-SUB URL
                        # --------------------------------------------------

                        sub_sub_url = sub_sub_link.xpath("./@href").get()

                        # --------------------------------------------------
                        # VALIDATE
                        # --------------------------------------------------

                        if not sub_sub_name:
                            continue

                        if not sub_sub_url:
                            continue

                        sub_sub_name = sub_sub_name.strip()

                        sub_sub_url = urljoin(response.url, sub_sub_url)

                        # --------------------------------------------------
                        # DUPLICATE CHECK
                        # --------------------------------------------------

                        sub_sub_key = (sub_sub_name.lower(), sub_sub_url)

                        if sub_sub_key in seen_sub_subcategories:
                            continue

                        seen_sub_subcategories.add(sub_sub_key)

                        print()
                        print("    SUB-SUB CATEGORY")
                        print("    NAME:", sub_sub_name)
                        print("    URL:", sub_sub_url)

                        # --------------------------------------------------
                        # ADD SUB-SUB CATEGORY
                        # --------------------------------------------------

                        sub_subcategories_data.append(
                            {
                                "category_name": sub_sub_name,
                                "category_url": sub_sub_url,
                                "category_level": 3,
                            }
                        )

                # --------------------------------------------------
                # ADD SUB CATEGORY
                # --------------------------------------------------

                subcategories_data.append(
                    {
                        "category_name": sub_name,
                        "category_url": sub_url,
                        "category_level": 2,
                        "subcategories": sub_subcategories_data,
                    }
                )

            # --------------------------------------------------
            # SEND MAIN CATEGORY TO PIPELINE
            # --------------------------------------------------

            print()
            print("SENDING CATEGORY TO PIPELINE:", main_name, flush=True)
            # exit()

            # --------------------------------------------------
            # IMPORTANT:
            # MAIN CATEGORY PARENT ID = 1
            # --------------------------------------------------

            yield CategoryItem(
                category_name=main_name,
                category_url=main_url,
                parent_id=1,
                category_table=self.category_table,
                # site_id=self.site_id,
                # site_code=self.site_code,
                category_level=1,
                subcategories=subcategories_data,
            )
