import scrapy
from ...items import ProductItem, CategoryDetailsItem, archivedetails
import sys
import pyodbc
import json
import re

# from ...database import site_config
from ...database.db import get_connection
from ...database.site_config import get_site_config
from ...database.site_config import get_conversion_rate


class ExampleSpider(scrapy.Spider):

    print("######## EXAMPLE SAMSMX FILE LOADED ########")

    name = "SAMSMX_prod"
    allowed_domains = ["www.sams.com.mx"]
    start_urls = ["https://www.samsclub.com.br/"]

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "max-age=0",
        "cookie": 'vtex-search-anonymous=21775e94ebbb4124bd725d831de42ac1; _fbp=fb.2.1790676842383.27277183260852257; _ga=GA1.1.67205339.1790676844; __privaci_cookie_consent_uuid=d0b6e24b-04c7-4214-bb92-d249c03db6e0:24; __privaci_cookie_consent_generated=d0b6e24b-04c7-4214-bb92-d249c03db6e0:24; FPID=FPID2.3.8NOj%2BRrOUD%2BrV1RINcUZNSeQ%2BaC3%2BlULsrlmijmQgy8%3D.1790676844; FPLC=uvROX6bfvhLHbYzGAfPGx5Zx63kG%2FGUhraeNC%2FJmcS9JFhd196hC8PWrRbgaX1jYRz2%2BI1gqBAYCXtlJDl1wXBy1Pwuu4yG727poxGs4vUpLxt5vpmzzdClcV2HA%2Bw%3D%3D; FPAU=1.1.1759168099.1790676842; __privaci_cookie_consents={"consents":{"85":1,"86":1,"87":1,"88":1,"90":1,"131":0},"location":"MH#IN","lang":"en","gpcInBrowserOnConsent":false,"gpcStatusInPortalOnConsent":false,"status":"record-consent-success","implicit_consent":false,"ct":4,"ts":1790676869}; __privaci_latest_published_version={"v":26,"sync":0,"kn":"","cid":0}; session-id=4086e1b7-55d8-4587-9722-f5f9825108e6; vtex-search-session=88ae87e844664576804bbddec7053d7c; cf_clearance=RC41snM.F6HP0joga9dVirF5pUA3cF2I8fk582yAkaA-1790746513-1.2.1.1-G.iYG36KOV.IzcQz9oVfO5frdLecW0ejAj8sTwPOMqgeh1kS71102.WwuQ4wfTJn2q2porMkdfPWL6xiUcDPmzGtCWsrSX_MsveV2tXElZPiiLTu4TjX21gaWGsC_74rROZNVDIoN.lFZQsfUAatQJQiVGeu_UDW.2OFMvWfArrAzSMfrModGWT0qq2Qz0aN9YTyTbQVjwrZOvbqzEs2ApvFVhyjSMNepuoZ5CyPSOniRAnWyMLl01l3.gIRPSbj8pAj2L.Da6lsAmipicfFxZGaU3ZbJg17pzRTIUZtcrtSNncGS8QRoLdMqHcKgR1YuRuFkZIM73QkHdNg36URAFneUSqCtOE4EKkTkYeWX6H3x5iKCzkP5P0ZZfMixneXMBV4pX_Rby2zhQuFt1F78CbevjkRSY9zLjCbOVSURfgUOh3DZqPFRfBJYMxtHWBDHYgs8ULuIfVz60Pxm7m5_w; __cf_bm=nkfbrpuJu1HEc0DvzMmWorwIILlWX.WCaAT9uq2NOuA-1790746513.1648438-1.0.1.1-uEpvEpcw8kpuQNDiAXphuqrxCecK9xmsusRY9PcoL7r2Ql2NEtpCK8CubjQBur64H7EyfmGqVJuNGWeMmtLTcfN8RTqVEC4yME5ecIzuAyJDotKWipiejQAFtKncd2Wf; __utmzzses=1; _clck=u6vxij%5E2%5Eg9w%5E0%5E2463; __utmzz=utmcsr=SEO|utmcmd=organic|utmccn=not set|utmctr=(not provided); _gcl_au=1.1.1759168099.1790676842.-.-.1790676842.1960647868.1790676842.1790746661; _ga_W2X18P93XW=GS2.1.s1790746516$o2$g1$t1790746661$j60$l0$h357390158; _uetsid=7ea24280bbee11f1954dad364518e744; _uetvid=7ea24da0bbee11f1910a1f9a41d696dd; FPGSID=1.1790746516.1790746661.G-W2X18P93XW.umHPClhCZLex2sBSCCElng; cookieAccepted=Essential|Analytics & Customization|Unclassified|Advertising|Essential|Performance & Functionality|; _clsk=mhj5bc%5E1790746662322%5E2%5E1%5Eh.clarity.ms%2Fcollect; ServerAwinChannelCookie=direct',
        "priority": "u=0, i",
        "sec-ch-ua": '"Chromium";v="154", "Google Chrome";v="154", "Not A(Brand";v="99"',
        "sec-ch-ua-arch": '"x86"',
        "sec-ch-ua-bitness": '"64"',
        "sec-ch-ua-full-version": '"154.0.8037.58"',
        "sec-ch-ua-full-version-list": '"Chromium";v="154.0.8037.58", "Google Chrome";v="154.0.8037.58", "Not A(Brand";v="99.0.0.0"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-model": '""',
        "sec-ch-ua-platform": '"Windows"',
        "sec-ch-ua-platform-version": '"19.0.0"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36",
    }

    # start_urls = ["https://www.bathandbodyworks.com.au/body-care"]
    async def start(self):
        print("######## START REQUESTS ########", flush=True)

        connection = get_connection()
        cursor = connection.cursor()

        site_id = 989
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
        sql = f"SELECT top 5 SubCategoryID,SubCategoryName,SubCategoryURL,CurrentVersion FROM {category_table} WITH (NOLOCK) WHERE SubCategoryID NOT IN (SELECT ParentCategoryID FROM {category_table} WHERE ParentCategoryID IS NOT NULL) AND PriceICCategoryID IS NOT NULL ORDER BY SubCategoryID"
        # sql = f"SELECT SubCategoryID,SubCategoryName,SubCategoryURL,CurrentVersion FROM SAMSMX_Categories WITH (NOLOCK) WHERE SubCategoryID=4"

        cursor.execute(sql)
        rows = cursor.fetchall()
        print("TOTAL CATEGORY URLS:", len(rows))
        # exit()
        self.site_code = site_code
        self.currentversion = currentversion
        for row in rows:

            cat_id = row[0]
            category_name = row[1]
            category_url = row[2]
            domain = "https://www.sams.com.mx"

            if category_url:
                if domain not in category_url:
                    category_url = domain + category_url

            # category_url = "https://www.sams.com.mx/browse/belleza-cuidado-personal-y-perfumeria/perfumes-y-fragancias/perfumes-para-mujer/30128_30142_30143"
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
        print("Parse CURRENT PAGE:", response.url)
        print("STATUS:", response.status)
        # print("STATUS:", response.text)
        print("======================================")
        # exit()

        cat_id = response.meta["cat_id"]
        category_name = response.meta["category_name"]
        category_url = response.meta["category_url"]
        currentversion = response.meta["currentversion"]
        site_id = response.meta["site_id"]
        site_code = response.meta["site_code"]
        usdequal = response.meta["usdequal"]
        category_table = response.meta["category_table"]
        product_count = ""
        print("########################################page")

        # ============================================================
        # GET __NEXT_DATA__
        # ============================================================

        # script = response.xpath(
        #     '//script[@id="__NEXT_DATA__" and @type="application/json"]/text()'
        # ).get()
        # print(script)
        # exit()
        # if not script:
        #     print("❌ __NEXT_DATA__ NOT FOUND", flush=True)
        #     return

        # try:
        #     data = json.loads(script)
        # except json.JSONDecodeError as e:
        #     print("❌ JSON ERROR:", e, flush=True)
        #     return

        # # ============================================================
        # # GET contentLayout
        # # ============================================================

        # content_layout = (
        #     data.get("props", {})
        #     .get("pageProps", {})
        #     .get("initialTempoData", {})
        #     .get("data", {})
        #     .get("contentLayout", {})
        # )

        # # ============================================================
        # # GET ALL MODULES
        # # ============================================================

        # modules = content_layout.get("modules", [])

        # print("TOTAL MODULES:", len(modules), flush=True)

        # # ============================================================
        # # LOOP EVERY MODULE
        # # ============================================================

        # product_urls = []

        # for module_index, module in enumerate(modules):

        #     print(f"\n========== MODULE [{module_index}] ==========", flush=True)

        #     configs = module.get("configs", {})

        #     if not configs:
        #         continue

        #     # ========================================================
        #     # GET productsConfig
        #     # ========================================================

        #     products_config = configs.get("productsConfig", {})

        #     if not products_config:
        #         continue

        #     # ========================================================
        #     # GET products[]
        #     # ========================================================

        #     products = products_config.get("products", [])

        #     print("PRODUCTS IN MODULE:", len(products), flush=True)

        #     # ========================================================
        #     # LOOP EVERY PRODUCT
        #     # ========================================================

        #     for product_index, product in enumerate(products):

        #         canonical_url = product.get("canonicalUrl")

        #         if canonical_url:

        #             print(
        #                 f"PRODUCT [{product_index}] CANONICAL URL:",
        #                 canonical_url,
        #                 flush=True,
        #             )

        #             product_urls.append(canonical_url)

        # # ============================================================
        # # FINAL RESULT
        # # ============================================================

        # print("\nTOTAL CANONICAL URLS:", len(product_urls), flush=True)

        # # ============================================================
        # # OPTIONAL: REMOVE DUPLICATES
        # # ============================================================

        # product_urls = list(dict.fromkeys(product_urls))

        # print("UNIQUE CANONICAL URLS:", len(product_urls), flush=True)
        product_urls = []

        script = response.xpath(
            '//script[@id="__NEXT_DATA__" and @type="application/json"]/text()'
        ).get()

        data = None

        # ============================================================
        # Try __NEXT_DATA__
        # ============================================================

        if script:

            try:
                data = json.loads(script)

            except json.JSONDecodeError:
                data = None

        # ============================================================
        # If __NEXT_DATA__ is not available,
        # find CollectionPage JSON-LD
        # ============================================================

        if not data:

            scripts = response.xpath(
                '//script[@type="application/ld+json"]/text()'
            ).getall()

            for script in scripts:

                try:
                    json_data = json.loads(script)

                except json.JSONDecodeError:
                    continue

                if (
                    isinstance(json_data, dict)
                    and json_data.get("@type") == "CollectionPage"
                ):

                    data = json_data
                    break

        # ============================================================
        # Process data
        # ============================================================

        if data:

            # --------------------------------------------------------
            # If data came from __NEXT_DATA__
            # Find all canonicalUrl values
            # --------------------------------------------------------

            if script and data:

                def find_canonical_urls(obj):

                    if isinstance(obj, dict):

                        for key, value in obj.items():

                            if key == "canonicalUrl" and value:

                                full_url = response.urljoin(value)

                                product_urls.append(full_url)

                            else:
                                find_canonical_urls(value)

                    elif isinstance(obj, list):

                        for item in obj:
                            find_canonical_urls(item)

                find_canonical_urls(data)

            # --------------------------------------------------------
            # If data is CollectionPage JSON-LD
            # Get product URLs from mainEntity.itemListElement
            # --------------------------------------------------------

            elif data.get("@type") == "CollectionPage":

                main_entity = data.get("mainEntity", {})

                if isinstance(main_entity, dict):

                    item_list = main_entity.get("itemListElement", [])

                    for item in item_list:

                        if not isinstance(item, dict):
                            continue

                        product_url = item.get("url")

                        if product_url:

                            full_url = response.urljoin(product_url)

                            product_urls.append(full_url)

        print("TOTAL PRODUCT URLS:", len(product_urls), flush=True)
        # exit()

        # ============================================================
        # CREATE REQUESTS
        # ============================================================

        for url in product_urls:

            if url.startswith("/"):
                url = response.urljoin(url)

            yield scrapy.Request(
                url=url,
                headers=self.headers,
                callback=self.product_parse,
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

        # next_page = response.css("li.van-pagination__item--next a::attr(href)").get()
        # next_page = response.css(
        #     "li.van-pagination__item--next:not(.van-pagination__item--disabled) a::attr(href)"
        # ).get()
        script1 = response.xpath(
            '//script[@id="__NEXT_DATA__" and @type="application/json"]/text()'
        ).get()

        if script1:
            try:
                data1 = json.loads(script1)

            except json.JSONDecodeError:
                data1 = None

            if data1:

                def find_max_page(obj):

                    if isinstance(obj, dict):

                        for key, value in obj.items():

                            if key == "maxPage":
                                return value

                            result = find_max_page(value)

                            if result is not None:
                                return result

                    elif isinstance(obj, list):

                        for item in obj:

                            result = find_max_page(item)

                            if result is not None:
                                return result

                    return None

            max_page = find_max_page(data1)

            print("page number:", max_page)
            # exit()

            if max_page and max_page > 1:

                for page in range(2, max_page + 1):

                    next_page = response.url + f"?page={page}"

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
                currentversion = response.meta["currentversion"]
                product_count = response.meta["product_count"]
                site_code = response.meta["site_code"]

                print("FINAL PRODUCT COUNT:", product_count, flush=True)

                # --------------------------------------------------
                # SEND CATEGORY DATA TO PIPELINE
                # --------------------------------------------------

                item = CategoryDetailsItem()

                item["cat_id"] = cat_id
                item["category_url"] = category_url
                item["category_table"] = category_table
                item["currentversion"] = currentversion
                item["product_count"] = product_count
                item["site_code"] = site_code

                print("######## CATEGORY UPDATE ITEM ########", flush=True)
                print("CAT ID:", cat_id, flush=True)
                print("CATEGORY URL:", category_url, flush=True)
                print("CATEGORY TABLE:", category_table, flush=True)
                print("CURRENT VERSION:", currentversion, flush=True)
                print("PRODUCT COUNT:", product_count, flush=True)

                yield item

            # item = archivedetails()

            # item["currentversion"] = currentversion
            # item["site_code"] = site_code

            # print("######## CATEGORY UPDATE ITEM ########", flush=True)
            # print("Site Code:", site_code, flush=True)
            # print("CURRENT VERSION:", currentversion, flush=True)

            # yield item

    def product_parse(self, response):
        print("###############PRODUCT_PARSE#####################")
        print("product_url:", response.url)
        product_url = response.url

        print("\n======================================")
        print("PPCURRENT PAGE:", response.url)
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
        # exit()

        json_ld_list = response.css('script[type="application/ld+json"]::text').getall()

        for json_text in json_ld_list:
            try:
                data = json.loads(json_text)

                # Process only Product JSON
                if data.get("@type") != "Product":
                    continue

                # Title
                title = data.get("name")

                # SKU / Product ID
                product_id = data.get("sku")

                # Images
                image = data.get("image")

                # Brand
                brand_data = data.get("brand", {})
                brand = brand_data.get("name") if isinstance(brand_data, dict) else None

                # Offers
                offers = data.get("offers", [])

                if isinstance(offers, list) and offers:
                    offer = offers[0]

                    price = offer.get("price")
                    product_url = offer.get("url")
                    availability = offer.get("availability", "")

                elif isinstance(offers, dict):
                    price = offers.get("price")
                    product_url = offers.get("url")
                    availability = offers.get("availability", "")

                else:
                    price = None
                    product_url = None
                    availability = ""

                # Availability
                is_available = 1 if "InStock" in availability else 0

                # Rating
                aggregate_rating = data.get("aggregateRating", {})

                if isinstance(aggregate_rating, dict):
                    rating = aggregate_rating.get("ratingValue")
                    noof_rating = aggregate_rating.get("reviewCount")
                else:
                    rating = None
                    noof_rating = None

                # Description
                description = data.get("description")

                print("TITLE:", title)
                print("PRICE:", price)
                print("URL:", product_url)
                print("IMAGE:", image)
                print("SKU:", product_id)
                print("BRAND:", brand)
                print("RATING:", rating)
                print("TOTAL RATINGS:", noof_rating)
                print("DESCRIPTION:", description)
                print("IS_AVAILABLE:", is_available)
                # print("MULTI IMAGES:", multiimages)
                print("-" * 80)
                # exit()

                item = ProductItem()

                item["title"] = title
                item["price"] = price
                item["link"] = product_url
                item["image"] = image
                item["sku"] = product_id
                item["brand"] = brand
                item["rating"] = rating
                item["product_rating"] = rating
                item["product_total_ratings"] = noof_rating
                item["description"] = description
                item["cat_id"] = cat_id
                item["category_name"] = category_name
                item["category_url"] = category_url
                item["currentversion"] = currentversion
                item["site_id"] = site_id
                item["site_code"] = site_code
                item["usdequal"] = usdequal
                item["category_table"] = category_table
                item["is_available"] = is_available

                yield item

            except json.JSONDecodeError:
                continue
