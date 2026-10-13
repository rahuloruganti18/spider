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

    print("######## EXAMPLE BBWIT FILE LOADED ########")

    name = "chnl_prod"
    allow_domains = ["https://www.chanel.com/it/"]

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "en-US,en;q=0.9,hi;q=0.8,fr;q=0.7",
        "cookie": "akacd_maintenance_ONE_SWISS_IN=2147483647~rv=31~id=c731d1931a1f616f980c9385d3d55a66; isClient=false; segment=none; OptanonAlertBoxClosed=2026-08-14T07:43:40.775Z; _gcl_au=1.1.1169011606.1786693421; _ga=GA1.1.894516225.1786693421; _cs_c=0; _fbp=fb.1.1786693422596.31170015736422633; _ga_chanel=GA1.1.894516225.1786693421; boutiqueApp=false; akacd_maintenance-ONE-EMEA-ECOMM=2147483647~rv=24~id=2ede55ebca81014d3d20f824fdbaef1e; mt.v=2.1024500110.1786693587564; __troRUID=54edb202-d76a-4eaf-a9c6-995d24cbd149; gig_bootstrap_4_DaVtG7pNrGVLgk9f-lZKCA=eu-gsso-login_ver4; chanel_it-cart=cf8f59d9-ac2f-4019-868a-bb86879fa0f7; gig_bootstrap_4_DUnWmJ8jidvh4SbBK3h5mg=in-gsso-login_ver4; chanel_in-cart=99dc710b-39aa-45cb-8997-3d126a23fa4a; country=IN; _abck=B6B4D94DB474B4D54282666A75ACB2AD~0~YAAQspUjFwIz8tSgAQAAi0K/7BCu2RdRn3/kuF0TDvbhujbKDW2vwav4E0jem53jnemhnj7nvbSl8KjmnmVg68l7SGV/9Y/F6y8K1q8O0yhWD+ghpRoB7qAE261JVhQZPh59dkVZfWmSsd7jssKKcAWxgpOny05GJKQlaf4GtgY8juljMZ2vDCtCq4Q9FNy5k/9acoWRw1+Nxu64tkGaICbXcL/ghB+UqBIZV5zSWU20Q7IuBhL7XaNxZWBTcWiFRLYXCqah99GnzVC1GihijMMXMSy28e8A7U9BVKBiQAFCt/j+UuYKp2pvRjC60hhQBXSwcI6CZOgqougaOOptxMBuPowdR9YRRtScaZUxReK99WRk9VgszLbP95Ya49D/wrledfD5IkRstQsABcCOJFSPpt2E/o6l1OzCfFwh7bQGKxbRzU05JJNLA1WAOHGLCT9CcztOtO5oMGZWPTgcymL8TQofvjbn8GG6HUrkWnVqgo8idxLPU1gRIQLluR4u8hGQI96epBQjY8uqgRHbGERMlGeITeqy7g3unZhJJGzXl0VYeCqVKyH1j6V8VCiTY6YaDTt5OUOgZ4RWIdiQzbs21RvHEHbo5NCjTij0ZwweQMEwUPG36HY3HNSURpsWVuBF2gVO1bLy/hijBAtwkw9K4pq0gAomgGY=~-1~-1~-1~AAQAAAAG%2f%2f%2f%2f%2f4W8wq5Bb6TUZSboGJRZO%2fh2q3Yw8kdGZ4lon+qXKprff8QkF7t+yW3bTXHfgKsrkytt3pHZeY%2fgO4+9Mdm3UIISvpso7LPFrF3%2f~-1; __troSYNC=1; mt.viewprec_fnb=fnb; ak_bmsc=D6111A154882EE23C965FE5CFB2F9E63~000000000000000000000000000000~YAAQx7xWaB6sJ9OgAQAAcyg57QG0JHAPTrkTPbdw3RmXzMUZ57WS5JvR79hROAxXB6E2FiI96Qs2/o7MTEdgQxBQ/bnsdAl7bi+y6utjrGOchqHNvQFzgKsR5U/iw3y7twPRWti1WwMllVREw+kN9DY8kx4pPsc7csMXg6d6tzmzGlD6urGy+TL62TcqRNLcGI9B2CxGVbqlw7q59ZJ08V5hLhpGrf47KRc8B47Bo5UZMgDDfl8xXJJc6oT3Q0Jh/9FJDiIieRkiAGGlV1UXmDEowNacMvIYVtwJDbE001hb5FCJxJi+lqX13FEzKVOR5se1V7VArKZMKmBp3tJSMEGtHbKtGYEW3Xmhra8jIjiAl6ODVd0RFs4cFGZCJ4GfVAidbTGjbrfuLxoReG4XUnWSRetHWpXhmlBQ2rB7JmsEZvsqviZiONEyTyp//alA+sH9C44Isvuk1FISp+0GufK7t5EpnQqu; _cs_mk_ga=0.7850350629309505_1790686342287; cookieDCM=1790686342.4r6dkecv; _ga_H7PKJDNS6Q=GS2.1.s1790686342$o6$g0$t1790686342$j60$l0$h0; JSESSIONID=E4C24D1C5D8B89558EAC58A66C844006; bm_so=EE51EC43B079693F28FC02F0DC4F30ADEF9F836F0A2F5673579C9682A6FADDF0~YAAQspUjFwty+9SgAQAA7u9G7Qk2wSQgfJUch9edex6Csu6HzUKrVIYZoEzf6kKsrc86vNBXZSVX/xdwqp/XHwZfPw9nsuAWrhs6cWpqlcDCkmvL4WETqKPjNXG8wymMce/NFp3GLhkWUC19TknToUlObNyxoTuB9K//cAPwEJler39s2nNH/GJObYNo88unYhdzy0TJdwAnU9rDmmIUFrHZOmdm7gJihv35G5Qhb1HceikXKNsGp29GWSw5xPi7NzRHVfg97ail7IwF+d2pDLDvE4udsWrYR/rTUeizYGLGUEvLepgHVRJdmAoFydnlglnY98Aqe1jHKof8E47fKz2rvtoc8MAzWjj0s//FPzm/Z26fDT84xhKW/Qwr/DkXiuAaTgDW0AlswejynE8FzpAqJ4zFk9VsscHBEIU/IB5FcZYrtAPC2vp8BLvFu+HAn2QXJU2tkty39p1ve7qgBSZQCBjch0fR6twbPjlBSDg5031f~2; bm_sz=4B42AD04127CBEAAF764EB522F0746EF~YAAQspUjFw1y+9SgAQAA7u9G7QGAApdq9cA2Jjcdd9ragEwW4faGQxMCEE2HAnzgVr5xitv6dtpfph4TdsztEyM4ek+doELryfDKK6wh81XMuNgk4c3nh8hAKyFNE+H2kqD8rPGv1ovGdQGf0YO54tMseOGFsCLjpkOP9/Z3CmIi+Rmus1zNW1mtQ1hlPEVFICcXkgaDWC1gWtiGy6261vmqtkdF2B+TgZcuan6GWOxMQxW9VNZuvDrAkrQUdoCFKHzcL89y/VDGllx+9uQJ+cQ1HkWKFh9v0hCQ/MyXyUhtnX4IiGT48dogZbsVRQQzoQTPMRbXXqDLtncfkkeYYXEZ5pm2R1gSjB/FAZX5RLhMLfwiNqhRvQ9QtfEMJy1RklVh1e2BPwpcAlHhlt13Gog+WkvimdIl/Lt5QpHZ2c4G0Tdy8vsQcjf5mZFhLlBYxUfk9raLZB7Ct0/3PUuuuV2NHMOp/awuu+aHPXzLwAdzXbzpkX1Gwd7OegjknJqDjjdtLGJ7iHw9eTsUMuE1kq+1GvtvQzB5r5RNrwfI+d2gvMz6~3163449~3163459; AWSALB=jAfwZ2NT/H6C+MylBTSYCpRa/jW10g9WEDHuyOx6WtXY+IBePd4/mPtzuObtMdPxLMZwlAmpFsVH+e6oOPQqoxcoHOJg/gE1BluIDLIkK6zwe3TrZFPCZ+82i0BQ; AWSALBCORS=jAfwZ2NT/H6C+MylBTSYCpRa/jW10g9WEDHuyOx6WtXY+IBePd4/mPtzuObtMdPxLMZwlAmpFsVH+e6oOPQqoxcoHOJg/gE1BluIDLIkK6zwe3TrZFPCZ+82i0BQ; bm_s=YAAQspUjF0Vy+9SgAQAAf/RG7QapxpUFFFjyabag/5WDLN0c1GVWcWCkGFd/qFKnJtSdDH+NgeCac6EMkectxZGBZdXCkfau019m8nBMK5qL3SlITjhHOyUZK0WkAUNmhEH4HMtAW8GO0rioG+KodAg8VLrSAe4hT2PoVGWZcNksZoIZaXuFoY5/ccPi7z6ueVxvq+b8RNpEL9mLcaVkv98w+KGJOEYnw9Htj8INEXJbMcrN5k5hN+9kXlok8kiMApvHM3GOfvfOiF7dXzSfjJdtnsfEdt7iacv31jK3LhYbSJlloMuNCC5Jz1tEFuTtP++yzFqhI5w98CJtlHAWQhwuWcugDCvVjbu7b416OajQcv/uLz0HoGYaKXKTfyzDPr75HPY1KogXclYmjfkDiMZKfaS3xOk0vSyoNzkLojIo88lyfr7ZjG6e1UfWC+4C99TXVUwYAQjkyVgEwdBAlN2q6b3cgszk/r4NQZJW+U0SP1K6UTKjAjavi5G0uLZNPJeB8CGB1IPaCqgjRBRpknHFS2kxdVNF0/be7BNQF6AgPoay41UH6hlC5CVSN2e4+7EcOCANRjEzozhwGwVR6DNLHhAcrtS1oPRlitbGFu+7n2nh1FAxtp+wmSPnQ/Jx9fptlKeOxGOY0yJFF/wtTr8apQ+9YLmR08xsiVx4/MtPpzi6At0B6hqdq78bxXKG7KNP27IVzvPKZK/m5K6srpW5IcpSlvwof6NRG5WsPzjN32m0/T6G4i0wDZ7drhzEhnIDhRkskT3aTv3oMc+o3Bd9sdEiajLHAjPLEH+bt9HuOifVhiYsri/TmtMTA15f7+IBGVyALB1Avguqz8J1wQEpPYoc8VJQ1//kV+1PFJT5f9dy0IV3RKuAr7lYsyF+c1+8syT5bPNXA2+nyjg7QKYLphnS9dJq0X4D1lYjrxFDyGudSM+/9BQjLn/L0zUElLLW2ZTdvQozQOqR59jLCMjyo8AksDitSZpK3oLh3DPWb8ogTCkTJfrZcpBVxespjeqQJ8jumoJZPHH8kxQUMyj3ojUffNT0UxCnAaCpf1bQ1rGhoVD16kj9cFjPFyIWEflMeLabp7/mci/r0DN6SnFHfkyYz23LAhho4GIVSJBf+ykMvNBjF0IE+w==; OptanonConsent=isGpcEnabled=0&datestamp=Tue+Sep+29+2026+18%3A37%3A26+GMT%2B0530+(India+Standard+Time)&version=202411.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=3d0cd645-cf19-4162-8ad5-4f0c99a7babf&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=1%3A1%2C2%3A1%2C3%3A1%2C4%3A1&intType=1&geolocation=IN%3BEU&AwaitingReconsent=false; bm_lso=EE51EC43B079693F28FC02F0DC4F30ADEF9F836F0A2F5673579C9682A6FADDF0~YAAQspUjFwty+9SgAQAA7u9G7Qk2wSQgfJUch9edex6Csu6HzUKrVIYZoEzf6kKsrc86vNBXZSVX/xdwqp/XHwZfPw9nsuAWrhs6cWpqlcDCkmvL4WETqKPjNXG8wymMce/NFp3GLhkWUC19TknToUlObNyxoTuB9K//cAPwEJler39s2nNH/GJObYNo88unYhdzy0TJdwAnU9rDmmIUFrHZOmdm7gJihv35G5Qhb1HceikXKNsGp29GWSw5xPi7NzRHVfg97ail7IwF+d2pDLDvE4udsWrYR/rTUeizYGLGUEvLepgHVRJdmAoFydnlglnY98Aqe1jHKof8E47fKz2rvtoc8MAzWjj0s//FPzm/Z26fDT84xhKW/Qwr/DkXiuAaTgDW0AlswejynE8FzpAqJ4zFk9VsscHBEIU/IB5FcZYrtAPC2vp8BLvFu+HAn2QXJU2tkty39p1ve7qgBSZQCBjch0fR6twbPjlBSDg5031f~2~1790687246339; __trossion=1786693589_1800_5_54edb202-d76a-4eaf-a9c6-995d24cbd149%3A1790678392_54edb202-d76a-4eaf-a9c6-995d24cbd149%3A1790686349_1790687246_10_; mt.fnbVisitCount=13; _cs_id=b5422955-e9bb-a84b-8414-270b20772c1e.1786693422.8.1790687248.1790686342.1752673093.1820857422109.1.x; _cs_s=11.0.U.9.1790689194023; _cs_s_ctx=%7B%22firstViewTime%22%3A1790686342904%2C%22firstViewUrl%22%3A%22https%3A%2F%2Fwww.chanel.com%2Fin%2F%22%2C%22sessionReferrer%22%3A%22https%3A%2F%2Fwww.chanel.com%2Fit%2Fprofumi%2Fla-collezione-coco%2Fc%2F7x3x6%2F%22%7D; bm_sv=004E12A392AF701624316A6DF8372CE6~YAAQtJUjF+CmDuegAQAA0IRJ7QEIu6O3YbrDCPdsRn+kmd+LnVgPfbQ586wRysgZ5ldzvocidcAyxzeMhXw9hGSfQdZAvoO8QomWJ3mKc4I8kpQlstQevIxY6c/jLP4kOctouQMhIoDGUeKeqjXNKYYpC/U70/jXQiXOknN0DwuTMEQrF9FCeUY0hfafBPjOstDbmMRuc/K6uGhYBlwNpaz5NkaYppTk4wQIaLD9jiokj/e0gkgeG+zyqvUl+TiIqZf/GKDjvROPKw==~1; _ga_10KWT1B3BD=GS2.1.s1790686348$o5$g1$t1790687414$j49$l0$h0",
        "priority": "u=0, i",
        "referer": "https://www.chanel.com/it/",
        "sec-ch-ua": '"Google Chrome";v="153", "Not_A Brand";v="8", "Chromium";v="153"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36",
    }

    # start_urls = ["https://www.bathandbodyworks.com.au/body-care"]
    async def start(self):
        print("######## START REQUESTS ########", flush=True)

        connection = get_connection()
        cursor = connection.cursor()

        site_id = 979
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
        sql = f"SELECT top 1 SubCategoryID,SubCategoryName,SubCategoryURL,CurrentVersion FROM {category_table} WITH (NOLOCK) WHERE SubCategoryID NOT IN (SELECT ParentCategoryID FROM {category_table} WHERE ParentCategoryID IS NOT NULL) AND PriceICCategoryID IS NOT NULL ORDER BY SubCategoryID"

        cursor.execute(sql)
        rows = cursor.fetchall()
        print("TOTAL CATEGORY URLS:", len(rows))
        # exit()
        self.site_code = site_code
        self.currentversion = currentversion
        for row in rows:

            cat_id = row[0]
            category_name = row[1]
            # category_url = row[2]
            category_url = (
                "https://www.chanel.com/it/profumi/la-collezione-coco/c/7x3x6/"
            )
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
        print("STATUS:", response.text)
        print("======================================")
        exit()

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

        json_ld = response.css('script[type="application/ld+json"]::text').getall()

        for json_text in json_ld:
            try:
                data = json.loads(json_text)

                # if data.get("@type") == "ItemList":
                #     print("ITEMLIST JSON FOUND")

                #     # Proceed with your ItemList processing here
                #     item_list = data
                # Process only ItemList JSON
                if data.get("@type") != "ItemList":
                    continue

                products = data.get("itemListElement", [])

                # Take only ONE product URL
                product = next(
                    (p for p in products if p.get("@type") == "ItemList"), None
                )

                if product:
                    product_url = product.get("url")

                    # Get window.pulsTranslations script
                    translation_script = response.xpath(
                        '//script[contains(text(), "window.pulsTranslations")]/text()'
                    ).get()

                    if translation_script:
                        try:
                            # Get JSON after window.pulsTranslations=
                            json_part = (
                                translation_script.split("window.pulsTranslations=", 1)[
                                    1
                                ]
                                .split(";", 1)[0]
                                .strip()
                            )

                            translations = json.loads(json_part)

                            # Get every p_<id>
                            product_ids = [
                                key.replace("p_", "")
                                for key in translations[0]
                                if key.startswith("p_")
                            ]

                            # Add every ID to the ONE URL
                            product_urls = []
                            count = 0
                            for product_id in product_ids:
                                product_url = (
                                    f"{product_url.rstrip('/')}/p/{product_id}"
                                )
                                product_urls.append(product_url)

                                print(f"{count}:PRODUCT URL:", product_url, flush=True)
                                count += 1
                                # yield scrapy.Request(
                                #     url=product_url,
                                #     # headers=self.headers,
                                #     callback=self.product_parse,
                                #     meta={
                                #         "cat_id": cat_id,
                                #         "category_name": category_name,
                                #         "category_url": category_url,
                                #         "currentversion": currentversion,
                                #         "site_id": site_id,
                                #         "site_code": site_code,
                                #         "usdequal": usdequal,
                                #         "category_table": category_table,
                                #         "handle_httpstatus_all": True,
                                #         "product_count": product_count,
                                #     },
                                #     dont_filter=True,
                                # )
                            exit()

                        except Exception as e:
                            print("TRANSLATION JSON ERROR:", e, flush=True)

            except json.JSONDecodeError:
                continue

        # next_page = response.css("li.van-pagination__item--next a::attr(href)").get()
        # next_page = response.css(
        #     "li.van-pagination__item--next:not(.van-pagination__item--disabled) a::attr(href)"
        # ).get()
        next_page = response.css('link[rel="next"]::attr(href)').get()

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
                images = data.get("image", [])

                if isinstance(images, str):
                    images = [images]

                image = images[0] if images else None

                # Multi images
                multiimages = " | ".join(images) if images else None

                # Brand
                brand_data = data.get("brand", {})
                brand = brand_data.get("name") if isinstance(brand_data, dict) else None

                # Offers
                offers = data.get("offers", {})

                if isinstance(offers, dict):
                    price = offers.get("price")
                    product_url = offers.get("url")
                else:
                    price = None
                    product_url = data.get("url")

                availability = data.get("offers", {}).get("availability", "")
                is_available = 1 if "InStock" in availability else 0

                # Rating
                aggregate_rating = data.get("aggregateRating", {})

                if isinstance(aggregate_rating, dict):
                    rating = aggregate_rating.get("ratingValue")
                    noof_rating = aggregate_rating.get("ratingCount")
                else:
                    rating = None
                    noof_rating = None

                # Description
                description = data.get("description")

                # Ingredients
                # Not available in this Product JSON-LD
                ingredients = None
                description_container = response.css(
                    "div.desktop-product-details.markdown noscript div.p-3"
                )

                # Description
                description = " ".join(
                    description_container.css("h2::text, p::text, li::text").getall()
                ).strip()

                # Ingredients
                ingredients = description_container.xpath(
                    ".//p[b[contains(text(), 'Ingredients:')]]/following-sibling::p[1]/text()"
                ).get()

                if ingredients:
                    ingredients = ingredients.strip()

                # Quantity / Size
                # Not available in this Product JSON-LD
                size = None

                # print("TITLE:", title)
                # print("PRICE:", price)
                # print("URL:", product_url)
                # print("IMAGE:", image)
                # print("SKU:", product_id)
                # print("BRAND:", brand)
                # print("RATING:", rating)
                # print("TOTAL RATINGS:", noof_rating)
                # print("DESCRIPTION:", description)
                # print("INGREDIENTS:", ingredients)
                # print("MULTI IMAGES:", multiimages)
                # print("SIZE:", size)
                # print("-" * 80)

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
                item["ingredients"] = ingredients
                item["multiimages"] = multiimages
                item["qty"] = size
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
