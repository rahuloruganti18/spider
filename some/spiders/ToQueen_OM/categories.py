import scrapy
import sys
from urllib.parse import urljoin

from ...items import CategoryItem


class LOOKSUKCategoriesSpider(scrapy.Spider):

    name = "toqueen_cat"

    allowed_domains = ["https://toqueen.com/en/"]
    start_urls = ["https://toqueen.com/en/"]

    # ------------------------------------------------------
    # SITE DETAILS
    # ------------------------------------------------------

    # site_id = 1
    site_code = "QUEENOM"
    category_table = "QUEENOM_Categories"

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

        # ==================================================
        # CATEGORY EXTRACTION USING XPATH
        # ==================================================

        categories = []

        seen_categories = set()

        # ==================================================
        # MAIN CATEGORIES - LEVEL 1
        # ==================================================

        main_categories = response.xpath('//ul[@id="menu-header-link"]/li')

        print("MAIN CATEGORY COUNT:", len(main_categories), flush=True)

        for main_li in main_categories:

            # --------------------------------------------------
            # MAIN CATEGORY NAME AND URL
            # --------------------------------------------------

            main_name = main_li.xpath(
                'normalize-space(./a[1]//span[@class="nav-link-text"])'
            ).get()

            main_url = main_li.xpath("./a[1]/@href").get()

            if not main_name:
                continue

            main_name = main_name.strip()

            if not main_url:
                continue

            main_url = response.urljoin(main_url)

            # --------------------------------------------------
            # FIND SUBCATEGORIES
            # --------------------------------------------------

            sub_categories = main_li.xpath(
                './div[contains(@class, "wd-dropdown")]'
                '//ul[contains(@class, "wd-sub-menu")]/li'
            )

            # Skip categories without subcategories, such as Shop
            # if not sub_categories:
            #     print(
            #         "SKIPPING CATEGORY WITHOUT SUBCATEGORIES:",
            #         main_name,
            #         flush=True,
            #     )
            #     continue

            # --------------------------------------------------
            # DUPLICATE CHECK - MAIN CATEGORY
            # --------------------------------------------------

            main_key = (main_name.lower(), main_url)

            if main_key in seen_categories:
                continue

            seen_categories.add(main_key)

            print()
            print("============================================")
            print("MAIN CATEGORY")
            print("NAME:", main_name)
            print("URL:", main_url)
            print("PARENT ID: 1")

            # ==================================================
            # SUBCATEGORIES - LEVEL 2
            # ==================================================

            subcategories = []

            seen_subcategories = set()

            print(
                "SUB CATEGORY COUNT:",
                len(sub_categories),
                flush=True,
            )

            for sub_li in sub_categories:

                # --------------------------------------------------
                # SUBCATEGORY NAME AND URL
                # --------------------------------------------------

                sub_name = sub_li.xpath("normalize-space(./a[1])").get()

                sub_url = sub_li.xpath("./a[1]/@href").get()

                if not sub_name:
                    continue

                sub_name = sub_name.strip()

                if not sub_url:
                    continue

                sub_url = response.urljoin(sub_url)

                # --------------------------------------------------
                # DUPLICATE CHECK - SUBCATEGORY
                # --------------------------------------------------

                sub_key = (sub_name.lower(), sub_url)

                if sub_key in seen_subcategories:
                    continue

                seen_subcategories.add(sub_key)

                print()
                print("--------------------------------------------")
                print("SUB CATEGORY:", sub_name)
                print("URL:", sub_url)

                # ==================================================
                # SUB-SUBCATEGORIES - LEVEL 3
                # ==================================================

                sub_subcategories = []

                seen_sub_subcategories = set()

                sub_sub_links = sub_li.xpath(
                    './ul[contains(@class, "sub-sub-menu")]/li'
                )

                for sub_sub_li in sub_sub_links:

                    # --------------------------------------------------
                    # SUB-SUBCATEGORY NAME AND URL
                    # --------------------------------------------------

                    sub_sub_name = sub_sub_li.xpath("normalize-space(./a[1])").get()

                    sub_sub_url = sub_sub_li.xpath("./a[1]/@href").get()

                    if not sub_sub_name:
                        continue

                    sub_sub_name = sub_sub_name.strip()

                    if not sub_sub_url:
                        continue

                    sub_sub_url = response.urljoin(sub_sub_url)

                    # --------------------------------------------------
                    # DUPLICATE CHECK - SUB-SUBCATEGORY
                    # --------------------------------------------------

                    sub_sub_key = (
                        sub_sub_name.lower(),
                        sub_sub_url,
                    )

                    if sub_sub_key in seen_sub_subcategories:
                        continue

                    seen_sub_subcategories.add(sub_sub_key)

                    print(
                        "    SUB-SUB CATEGORY:",
                        sub_sub_name,
                        flush=True,
                    )

                    print(
                        "    URL:",
                        sub_sub_url,
                        flush=True,
                    )

                    # --------------------------------------------------
                    # ADD LEVEL 3 CATEGORY
                    # --------------------------------------------------

                    sub_subcategories.append(
                        {
                            "sub_sub_category_name": sub_sub_name,
                            "sub_sub_category_url": sub_sub_url,
                            "sub_sub_category_level": 3,
                        }
                    )

                # ==================================================
                # ADD LEVEL 2 CATEGORY
                # ==================================================

                subcategories.append(
                    {
                        "sub_category_name": sub_name,
                        "sub_category_url": sub_url,
                        "sub_category_level": 2,
                        "sub_subcategories": sub_subcategories,
                    }
                )

            # ==================================================
            # ADD MAIN CATEGORY TO LOCAL LIST
            # ==================================================

            categories.append(
                {
                    "category_name": main_name,
                    "category_url": main_url,
                    "category_level": 1,
                    "subcategories": subcategories,
                }
            )

            # ==================================================
            # SEND MAIN CATEGORY TO PIPELINE
            # ==================================================

            print()
            print("SENDING CATEGORY TO PIPELINE:", main_name, flush=True)
            print("SUBCATEGORY COUNT:", len(subcategories), flush=True)
            # print(categories)
            # exit()

            yield CategoryItem(
                category_name=main_name,
                category_url=main_url,
                parent_id=1,
                category_table=self.category_table,
                category_level=1,
                subcategories=subcategories,
            )
