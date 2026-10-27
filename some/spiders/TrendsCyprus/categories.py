import scrapy

from ...items import CategoryItem


class RetalierCategoriesSpider(scrapy.Spider):

    name = "trendscyp_cat"

    allowed_domains = ["trendscyprus.com"]
    start_urls = ["https://trendscyprus.com/"]

    # ------------------------------------------------------
    # SITE DETAILS
    # ------------------------------------------------------

    site_code = "TRENDSCYP"
    category_table = "TRENDSCYP_Categories"

    # ------------------------------------------------------
    # RECURSIVE SUBCATEGORY EXTRACTION
    # ------------------------------------------------------

    def extract_subcategories(self, parent_li, response, level=2):

        subcategories = []
        seen = set()

        child_items = parent_li.xpath('./ul[contains(@class, "mega-sub-menu")]/li')

        for child_li in child_items:

            name = child_li.xpath("normalize-space(./a[1])").get()

            url = child_li.xpath("./a[1]/@href").get()

            if not name or not url:
                continue

            name = name.strip()
            url = response.urljoin(url.strip())

            # Only include product category URLs.
            if "/product-category/" not in url.lower():
                continue

            key = (name.lower(), url)

            if key in seen:
                continue

            seen.add(key)

            print(
                f"{'  ' * level}LEVEL {level}: {name}",
                flush=True,
            )
            print(
                f"{'  ' * level}URL: {url}",
                flush=True,
            )

            nested_categories = self.extract_subcategories(
                child_li,
                response,
                level + 1,
            )

            # category = {
            #     "sub_category_name": name,
            #     "sub_category_url": url,
            #     "sub_category_level": level,
            # }

            # if level == 2:
            #     category["sub_subcategories"] = nested_categories
            # else:
            #     category["subcategories"] = nested_categories

            if level == 2:
                category = {
                    "sub_category_name": name,
                    "sub_category_url": url,
                    "sub_category_level": level,
                    "sub_subcategories": nested_categories,
                }
            else:
                category = {
                    "sub_sub_category_name": name,
                    "sub_sub_category_url": url,
                    "sub_sub_category_level": level,
                    "sub_subcategories": nested_categories,
                }

            subcategories.append(category)

        return subcategories

    # ------------------------------------------------------
    # MAIN PARSE
    # ------------------------------------------------------

    def parse(self, response):

        print("\n############################################")
        print("TRENDS CYPRUS CATEGORY SPIDER")
        print("STATUS:", response.status)
        print("URL:", response.url)
        print("############################################\n")

        seen_categories = set()

        # Find the main menu.
        menu = response.xpath('//ul[@id="mega-menu-main_menu"]')

        print("MAIN MENU FOUND:", len(menu), flush=True)

        if not menu:
            print(
                "ERROR: mega-menu-main_menu not found in HTML.",
                flush=True,
            )
            print(
                "Check whether the menu is loaded by JavaScript.",
                flush=True,
            )
            return

        main_categories = menu.xpath("./li")

        print(
            "TOTAL TOP-LEVEL MENU ITEMS:",
            len(main_categories),
            flush=True,
        )

        for main_li in main_categories:

            main_name = main_li.xpath("normalize-space(./a[1])").get()

            main_url = main_li.xpath("./a[1]/@href").get()

            print(
                "CHECKING MENU ITEM:",
                main_name,
                main_url,
                flush=True,
            )

            if not main_name or not main_url:
                continue

            main_name = main_name.strip()
            main_url = response.urljoin(main_url.strip())

            # Accept product-category URLs regardless of menu class.
            if "/product-category/" not in main_url.lower():
                print(
                    "SKIPPING NON-CATEGORY:",
                    main_name,
                    flush=True,
                )
                continue

            key = (main_name.lower(), main_url)

            if key in seen_categories:
                continue

            seen_categories.add(key)

            print("\nMAIN CATEGORY:", main_name)
            print("URL:", main_url)

            subcategories = self.extract_subcategories(
                main_li,
                response,
                level=2,
            )

            print(
                "SUBCATEGORY COUNT:",
                len(subcategories),
                flush=True,
            )

            yield CategoryItem(
                category_name=main_name,
                category_url=main_url,
                parent_id=1,
                category_table=self.category_table,
                category_level=1,
                subcategories=subcategories,
            )
