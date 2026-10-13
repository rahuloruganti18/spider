import scrapy
import sys
import json
from urllib.parse import urljoin
from ...database.db import get_connection

from ...items import CategoryItem


class TKMAXUKCategoriesSpider(scrapy.Spider):

    name = "tkmax_cat"

    allowed_domains = ["https://www.tkmaxx.com/uk/en/"]

    start_urls = ["https://www.tkmaxx.com/uk/en/"]
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9,hi;q=0.8,fr;q=0.7",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "cookie": 'OptanonAlertBoxClosed=2026-10-06T07:52:14.340Z; OptanonConsent=isGpcEnabled=0&datestamp=Tue+Oct+06+2026+15%3A28%3A20+GMT%2B0530+(India+Standard+Time)&version=202501.2.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=5d3ad21b-32a7-48a1-97c8-7fcbb9a1e5e6&interactionCount=2&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1&AwaitingReconsent=false&intType=1&geolocation=IN%3BMH; wp_vpc=#@\u0021sdv98c3P; PIM-SESSION-ID=PQMyTTCVSab3yrcK; ROUTE=.accstorefront-86c56d7475-pnntq; _gcl_au=1.1.1693290914.1791273134; _ga=GA1.1.1908251126.1791273132; _wt.mode-2718817=WT3bBXqdQOHqCg~; _scid=jyOII4FFDDSMhpMtZY6b4rM4RLyutTry; _tt_enable_cookie=1; _ttp=01M4835V052G138JH24N2972PE_.tt.1.1791273135109; _pin_unauth=dWlkPU5ERTJNRFkzWlRrdE1qWm1aaTAwTWpKaExUazBOalF0WW1ZeVpXTTJPV1ppWVRneg; tms_VisitorID=0p7y3drxe3; _sctr=1%7C1791225000000; _gtmeec=e30%3D; FPID=FPID2.3.CNAtxvUXVv7kYazD2LUDaQu7d%2FACSeH9kixhg4YozKQ%3D.1791273165; ApplicationGatewayAffinityCORS=696209e1c302a810311c6fc40f2d6b96; ApplicationGatewayAffinity=696209e1c302a810311c6fc40f2d6b96; _fbp=fb.1.1791273167620.119191150589289308; _uetsid=81fa8b50c15b11f1be0c9f7079fc83b2; _uetvid=81faf650c15b11f1872033cd36841c46; PreferredCountry=UK; _fbp=fb.1.1791273167620.119191150589289308; _ga_NMQ8PDK8P0=GS2.1.s1791275575$o2$g0$t1791275575$j60$l0$h0; JSESSIONID=Y21-97bd84d7-2bf8-453b-ba27-7766cd2723b3; minicartRefresh=false; FPLC=cBH%2Fg%2BbB7L5oYhmrFbFemTSmVwuWsp1Rw%2Bczj%2FD5%2BhmowvEUpATmfV19ANNTZIZkH46mAtogi%2FkseFHVkx%2Fx7d2auXreBDAn69GE26ys9sfadYG6SO8NZuiwVWe3Kw%3D%3D; tms_wsip=1; _bts=d0c72501-f572-4b40-817d-c3d5cb082430; _bti=%7B%22app_id%22%3A%22tkmaxx-eu%22%2C%22bsin%22%3A%22FkDe5Kuqod6ayI7O5e47WXpczn%2FUMQgTZ7MiD%2BIHuyzMIYCMH9jE2A71G0l03ZTZLaydVsK8ulfxADIWi0bMNw%3D%3D%22%2C%22external_ids%22%3A%7B%22zync%22%3A%2233ec1997-44ae-4332-a7a1-68a35d377c1f%3A1791273134.8240862%22%7D%2C%22is_identified%22%3Afalse%2C%22known_to_zeta%22%3Afalse%7D; _br_uid_2=uid%3D7627729139295%3Av%3D15.0%3Ats%3D1791273134787%3Ahc%3D5; bm_lso=3FAB9E01B674AF16357A80F0CA6C55A5BDD9E83EB0689A273FC56353F9FBA830~YAAQUJUjF2H8/uegAQAAa32UEAmuF2OboHwZ06f8qa/LwLXpKyXiTgUNS9pwtwjn9McgthpFZD30bER7Ssc+yDVRLqMMHOoqGNPpRukK0VVgTs4s9HkSo4JtXL52xB+1CD7RhGCF+u+fzbYbhrdMwXt/ZrTGdbLE+edSqUkQrC5CkKYnRc3cJPHz9D8TZU6/XBoILh1tl9GeLFOS1UAzr46FuQw0b33XcSUPryMlnLNj1rFuR3W039Te+ln3V9C9KJPuXlghBy3QDl6GljvzR0jpNODiwpRGK/k6oxkS8tvlNRV9NfBwfuDVwoRUAIuvJHnRZRwOdg8mAmWZmRbNzK8lcLWuyrLKwGK8jb25HEw4roi6lU7FgQCsJHObl7eBlPospJCoh3IJM8kBmdGcQIbekTIxUjpPnHRq97ja1Q+H0K/G1mzzTbOW4DK4HNl1cb0ejV2YPRNMUYvol2a5s31VfYvzmDtMkbtYJg==~4~1791279563635; bm_so=43EF809CEE32CB5B6F0A5DDA22C877678A09935D2C50D0E7E182A21FD3E69BE2~YAAQR5UjFxDG1tqgAQAA3jOmEAmerIvN9zrNGeRnhUh/PhkD9NqnPYk04poJnWmEyAyDagtUdus1k6Ksf/EzF/IN0Fv2TSK6+c2P1i0Do7b+qp375D1jyc0idJeYv0Df6EmJODlyOjUQ5/oyZowbb7yHewC6P492Tmv3phVWBTNn3LHL1UtrivBWRRhIkE4kokWW6I1ink6iRumTOJ5r0VeN0cLTz9znWkQNi0AEVrrE/+4Td19Z49/AMUIn6ARAMI0L4pV2x7pUlHqXLGO9MxoNdnfDRTpOJwRk/ubKnp2QVStzDFdLHp9DHLdgVtGuBOwYIVZSvL20rT5CC0hNa6Nm3YbdLr1asDvQA7IBouduaMwOJjJOAg6rGH4f2n0jQtlz0OxFlqNbq3m6CKU/6oBhfqoeGNjCk7tbAqSLYX5Emkthom6W5LOje0aOjGEKuc6XLpwBZrskWeaaVIBTdm1ktRD/8MHRQc/ZjQ==~7; ak_bmsc=1AF1A87CA1EC373A4F8416FB020AF887~000000000000000000000000000000~YAAQUJUjFy7d/+egAQAAXDimEAFDNkjheRoSkGSlOUh0G/ivJBTPZCGzAOuuBEiBPF/GIpcRzR6ntcxGED8vzdWlA1pNCMd510R2PvvJ0ub/SXDM7RrTaDn0OdiMgG2+LhuNPpdX6N6JiG5X9nZDXGkXQFS9gO00z1j2eB1/i+szDrmxDCNvt2p9zubZKNu67467xLHglfGvfkNEMP2Tp7kEkv1MevsiZyZuMV7aVcVmo+uzis3RSgf519haIX1wZ5AKQc0LaL9GAMWTRLHTmBMHh0TvMFkRTOTmfuw2fVt0oGXkuMwW+LfaJWvQARLvGcVF2/XG03y42/MvcBDlh5+MAxwQe59ocI2ubEU64BtQPO7L7fsJgHV30GLx12MAp36P; bm_sz=DCCAD91A6F675307FD11280F709A0063~YAAQUJUjF4ze/+egAQAAEk6mEAGY2RYVfIRSnZ8ko0ry2JqwTR0Iy3ZnHfm2KHaePgpWu0dYUBa9CJfUrpGqxR+t/NKUUkNYXNUp8uqotr3MJ4LGOYqNaImRMyFuj69lLvpD94mx/+hsoKqEqwKa/fnlPbEX722qeLQQHQ84foJyB51BXEXxTeXatsDCi5KKHQxsKSE3BNLGdEN0yCcwbL4TgLIrGGv1CDN4xfYsIdlbk23QejB3t3lcTdogLfDAMRD5ro37Oru4USHBNQHE405OMhWv6dvJsEln2PnUQcdxM+Gre3NS/FUmUmt+FMrqfS/hiLq3VzOu9Y6fx8vDU2C6071f2fnno63xMsClLiN3a+IeY8B/W3blVHrsUMSf3mYtNM7AGaKqhtyA0qFAt09Cwrapx2sk6R7ItISVql1UBKGXU9ETqliAz+QvbqWY0IeUOIqeHbzzW6NIncg39wEN4jckzeb2xdazNnWVUU7WzoUFFmuaXNkubFm+AI+kIimeQYIKbpBQbVOd/bkSuVYE~4601668~3486777; custdl=https://www.tkmaxx.com/uk/en/women/beauty/haircare/c/01060400; _wt.user-2718817=WT3uzKzGcUpcTkd5oaZru_5dWNNw_iiLj2fkC3NGWGE4_N2DNF68epESKolgv84V1-pD7t7zcFYja0iFj2DXvsDPPSWOhzlHrW38eZUJW9cmg6CYA-qGzh0EndbUyCtoh2V8UvkBn3AqZxd17GYBY9hncWBn7tnrc5nwulhwonwZqOMvtXrW5jmaI3Fub9CyBfS7pm_2uEl2GPZt4uVCeU4nVW27rCaIE7U0JN_UWXZlStVivDuLUyFDLhsJdxUHbvkffYwxvcPEsDUgw9R; _scid_r=jaOII4FFDDSMhpMtZY6b4rM4RLyutTryIHaoJg; __rtbh.uid=%7B%22eventType%22%3A%22uid%22%2C%22id%22%3A%22null%22%2C%22expiryDate%22%3A%222027-10-06T09%3A58%3A20.582Z%22%7D; __rtbh.lid=%7B%22eventType%22%3A%22lid%22%2C%22id%22%3A%22sZrA83iSTga31s6GKPzm%22%2C%22expiryDate%22%3A%222027-10-06T09%3A58%3A20.582Z%22%7D; bm_sv=C0E46B1D7E85EE6251B8B2363963B4D8~YAAQUJUjF0ff/+egAQAAC12mEAGquFQkf4Et0k13CA7hbrJMgm5+71EMAbnKl2rJFd0xuIdAIhwO2xcP+6LR9rTiybpTEjm78VXeDdVAVRFMeYAoBdS2VAbT0/SoSxPDBwOuSUlOqEdoU+DdAPTaAsb/nN3SVTN8KOfnAOddZMFMJX3G1cCE3FyALE78i3D2xmDDLk9D783lm8Pq8CvYY+pklxlaoYuD0SU5cS6R2xjmYhPLsl8LFXlPVXtgrnRc~1; _abck=6CF6FD64BC368D8C5317B44572A6B92F~0~YAAQUJUjF07f/+egAQAAil2mEBBlJ6OAI6gOX1X9Ccc9kd1r3gleNzs0Lyxn5KGmHk5jMQ51diH/Jonbd43quk9bTC/+I9Br9XiHfkLQID7hzX4m2tn35ywNaFwPx8khcYFlKYbmTwo6Mjw5sISYvP8A6QnSnmuVNSP1Y1aeJcrZsq4rKFh+u5/m3bkoR9L4ED+3TghTUkJ551tCIUya7lIiIanh463JjWiG0bix6GXnkYBX9838MCHq88u1JmEC05NCrdWS1Fj67jDKIhMtArdiIN9F2/1jvG5jH+J+q3qjNMRHVNIzjnpx1wpbNTMDAPbFUEope7YvH0fUdJShy+aGigfVJ+pRlcPZAes+eiBy/+U8mQ+3dWuyW5gMmTGCAM3MBlRLpOlhSCwJDikcDM7HI2guMcJi9b5Gtvi60Agj6mi3FrEOTQOmmSNIm2QUlRrKGtlWQ+dBHKMd1P4QnW6LIEDCfCuCCC+gudRi4NjJLriaXh6j7tpCDeKHvhXJ3c+hgj0MfEHXtLEupYcfG25cxOoAMnMdauP/OGMu5n6VyIwFiFQCga9zigyoxtspnTqRyVD0LQgnG5lmrAGFjfwfw3UhJZc1a4QO4f37BunivhxDQm1ywwDv9hpLiXpOMigq0unjQHKiq0iA/R1S85lUgYgBvBMBNTPn68M/0Qypz50i4hsb7lRp386VAzVjFXL3/hY2iCKxINSV3h9OJVQ8uQ==~-1~-1~1791284291~AAQAAAAG%2f%2f%2f%2f%2f5br1dX4rrTq959YeBnnpFZfHzZx57JfXA7ed4%2fTmEmKt7Rh%2fXF7XaB%2f8oMJRzKKWT99ECRVWAH5g+DMKixAKBXROAEieZamFD854mbek5N0xHqFk2BLBk9hcRVpWg%2fq6JD8j85GsyC0sv%2foBUuH74%2flYEvDmTPvFU2140JcAw%3d%3d~-1; ttcsid_D7L0STRC77U9IIEM7A00=1791279544857::-CJGdUmwwOywaLAi8xQJ.2.1791280701404.1; ttcsid=1791279544859::8qyvcF8-zWI8x3TUZSdd.2.1791280701404.0::1.1156526.1155850::0.0.0.0::0.0.0; RT="z=1&dm=www.tkmaxx.com&si=07483f50-0650-4612-badd-79155d54ceb4&ss=muwhl777&sl=1&tt=ja&bcn=%2F%2F684d0d42.akstat.io%2F&ld=owz7"; akavpau_www_tkmaxx_com=1791281009~id=4a0466da7adc1802f24bcd6b4d9519a8; bm_s=YAAQUJUjF/jg/+egAQAAMX6mEAYH9r38Muqj93kQZEGuVnOJl20atMQr69zfSvfy3iHwPVRp5pCCBpOVhWJZrKQFzsqEwtb93+19k8l/E1dZrL33fNkZfz+re6Am2NCaBmDR/POyz6lLDIGQSBN7JilwLaF91eMj3l/C4Db8xwPxnlr+Z0pUHsd8P6Ri+2qr0guHna28Yi+Fn/hMHx1BfaBxye8pGXW3jmEAHtawJXmh6JKdEPZahB4/ZQCc+e+isaBg5c2Tuy55WOK4WUfE8oUs5WH5d75Jw78zRzfGBLWK0viRZ0k4coX3BDSBFVssRaVYJdLmI+9MiqZf0e54HyLqGLjQmNjWzHXx9BNzD4eybWyALXQD7KHvH+vazD3Xtxq6EjMDrrFF29HrUwBsKG+NiZ5zNmkdR1QOpeFoiQOGq+ke0xvLmmXHKgBXWBYyg6vUUbtRva33fzzKHPNLK9DBacDqb0oERZTYKMoaQ97AFvknnCHrckSRh50mtJx9OvQ+3oRQKwhBsAyI/taVFDyV6CJU3MT+KcPAuowPqznxdWk3JKpDAfM8sFST2u2P+ltU3DuajxsK4dtiRG8W1z/uEG3orkQPBDMtVZ85Xl8vvSKgRoCGc5myK5H0P/5eFjJ97ojZ30ZFbXyhXMNyZeyp9Mxp6klsDrP8YrZo8TDZaH+nQIBfSGNDbddOENwGn2Ag57lQKGLhySj9mBGrm2HgZ+Z3qKO1taDiNiLVheF/1nI8yn4Sr30J+R+NQJe7XnmJDNXaP01MNbCOv9ETR7d4t65RyKhuTMdcoDpjL7dXa5apX40c2PiCaBOgyZCKAfqriVonFPZBb4iCOX9rceI5yeM+DlHHEZzDG7pjkg2ICY7yqf0zPTUDT2y09foN3/vvQW+J/59BtDFmPeCfqwn7lV7UZRrS38Ts2ZGnE4AefVeJ87JHMKK+2XRGz8MeDmfPu0bdGy44/MMHijsajIQhX15+anKxY1u6yCayZRMRKq8+RPwv0mp/620dDs4LJitOrO0IZf7R05xhvKq+VJNq2ERTY6XDvkK3l1TBbfEHfkVNWQefOe8Ckh2k/xZFa7Z5BZWVuf9xYIDKFeLXQ6RQxlgBfi2sy6AX; _ga_XSRWRL3E5V=GS2.1.s1791279540$o2$g1$t1791280711$j39$l0$h0',
        "Referer": "https://www.tkmaxx.com/uk/en/",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="154", "Google Chrome";v="154", "Not A(Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.site_id = 993
        self.site_code = "TKMAXUK"
        self.category_table = "TKMAXUK_Categories"

    async def start(self):
        print("######## START REQUESTS ########", flush=True)

        connection = get_connection()
        cursor = connection.cursor()
        category_url = "https://www.tkmaxx.com/uk/en/"

        yield scrapy.Request(
            url=category_url,
            headers=self.headers,
            callback=self.parse,
            meta={
                "handle_httpstatus_all": True,
                "product_count": 0,
            },
            dont_filter=True,
        )
        # exit()

        cursor.close()
        connection.close()

    def parse(self, response):

        print()
        print("############################################")
        print("TKMAX CATEGORY SPIDER")
        print("############################################")
        print("STATUS:", response.status)
        # print("TEXT:", response.text)
        print("URL:", response.url)
        print()

        for l1 in response.css("li.l1-navigation-item"):

            category_name = l1.css(":scope > a::attr(title)").get()

            category_url = l1.css(":scope > a::attr(href)").get()

            if category_name and category_url:

                category_url = response.urljoin(category_url)

                print("CATEGORY:", category_name, flush=True)
                print("CATEGORY URL:", category_url, flush=True)
