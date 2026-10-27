import scrapy

from ...items import CategoryItem


class RetalierCategoriesSpider(scrapy.Spider):

    name = "princessqtr_cat"

    allowed_domains = ["https://princesscosmeticsqa.com/"]
    start_urls = ["https://princesscosmeticsqa.com/"]

    # ------------------------------------------------------
    # SITE DETAILS
    # ------------------------------------------------------

    site_code = "PCQTR"
    category_table = "PCQTR_Categories"

    # ------------------------------------------------------
    # RECURSIVE SUBCATEGORY EXTRACTION
    # ------------------------------------------------------

    def extract_subcategories(self, parent_li, response, level=2):

        subcategories = []
        seen = set()

        # Find the dropdown belonging directly to this parent item.
        dropdowns = parent_li.xpath(
            './div[contains(concat(" ", normalize-space(@class), " "), '
            '" f-site-nav__dropdown ")]'
        )

        for dropdown in dropdowns:

            # Select only direct list items of each dropdown UL.
            child_items = dropdown.xpath("./div/ul/li | ./ul/li | " "./div/div/ul/li")

            for child_li in child_items:

                # Only process navigation sub-items.
                classes = child_li.xpath("normalize-space(@class)").get() or ""

                if "f-site-nav__sub-item" not in classes.split():
                    continue

                name = child_li.xpath(
                    "normalize-space(./a[1]//span[not("
                    'contains(concat(" ", normalize-space(@class), " "), '
                    '" f-site-nav__arrow "))][1])'
                ).get()

                url = child_li.xpath("./a[1]/@href").get()

                if not name:
                    name = child_li.xpath("normalize-space(./a[1])").get()

                if not name or not url:
                    continue

                name = name.strip()
                url = response.urljoin(url.strip())

                if url.startswith("javascript:") or url.endswith("#"):
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

                # Recursively extract nested dropdowns.
                nested_categories = self.extract_subcategories(
                    child_li,
                    response,
                    level + 1,
                )

                # ------------------------------------------
                # BUILD CATEGORY DICTIONARY
                # ------------------------------------------

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
    # PARSE MAIN NAVIGATION
    # ------------------------------------------------------

    def parse(self, response):

        print()
        print("############################################")
        print("CATEGORY SPIDER")
        print("############################################")
        print("STATUS:", response.status)
        print("URL:", response.url)
        print()

        seen_categories = set()

        # Find top-level navigation items.
        # Exclude items nested inside another navigation item.
        main_categories = response.xpath(
            '//li[contains(concat(" ", normalize-space(@class), " "), '
            '" f-site-nav__item ")]'
            '[not(ancestor::li[contains(concat(" ", '
            'normalize-space(@class), " "), " f-site-nav__item ")])]'
        )

        print(
            "MAIN CATEGORY COUNT:",
            len(main_categories),
            flush=True,
        )

        for main_li in main_categories:

            main_name = main_li.xpath(
                "normalize-space(./a[1]//span[not("
                'contains(concat(" ", normalize-space(@class), " "), '
                '" f-site-nav__arrow "))][1])'
            ).get()

            main_url = main_li.xpath("./a[1]/@href").get()

            if not main_name:
                main_name = main_li.xpath("normalize-space(./a[1])").get()

            if not main_name or not main_url:
                continue

            main_name = main_name.strip()
            main_url = response.urljoin(main_url.strip())

            if main_url.startswith("javascript:") or main_url.endswith("#"):
                print(
                    "SKIPPING INVALID URL:",
                    main_name,
                    main_url,
                    flush=True,
                )
                continue

            main_key = (main_name.lower(), main_url)

            if main_key in seen_categories:
                continue

            seen_categories.add(main_key)

            print()
            print("============================================")
            print("MAIN CATEGORY:", main_name)
            print("URL:", main_url)
            print("PARENT ID: 1")

            # Extract all nested categories.
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

            # ------------------------------------------
            # SEND TO PIPELINE
            # ------------------------------------------

            yield CategoryItem(
                category_name=main_name,
                category_url=main_url,
                parent_id=1,
                category_table=self.category_table,
                category_level=1,
                subcategories=subcategories,
            )
