# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

"""from dataclasses import dataclass


@dataclass
class SomeItem:
    # define the fields for your item here like:
    # name: str | None = None
    pass"""

import scrapy


class CategoryItem(scrapy.Item):

    category_name = scrapy.Field()
    category_url = scrapy.Field()
    parent_id = scrapy.Field()
    category_table = scrapy.Field()
    site_id = scrapy.Field()
    site_code = scrapy.Field()
    subcategories = scrapy.Field()
    category_level = scrapy.Field()
    body = scrapy.Field()


class ProductItem(scrapy.Item):

    title = scrapy.Field()
    price = scrapy.Field()
    link = scrapy.Field()
    img = scrapy.Field()
    sku = scrapy.Field()

    cat_id = scrapy.Field()
    category_name = scrapy.Field()
    category_url = scrapy.Field()
    currentversion = scrapy.Field()
    site_id = scrapy.Field()
    site_code = scrapy.Field()
    usdequal = scrapy.Field()
    usprice = scrapy.Field()
    category_table = scrapy.Field()


class DeataisItem(scrapy.Item):

    description = scrapy.Field()
    ingredients = scrapy.Field()
    ingre_plain = scrapy.Field()
    nutration = scrapy.Field()
    nutra_plain = scrapy.Field()
    brand = scrapy.Field()
    multiimages = scrapy.Field()
