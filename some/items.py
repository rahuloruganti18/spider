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


class CategoryDetailsItem(scrapy.Item):

    cat_id = scrapy.Field()
    site_code = scrapy.Field()
    category_url = scrapy.Field()
    category_table = scrapy.Field()
    currentversion = scrapy.Field()
    product_count = scrapy.Field()


class ProductItem(scrapy.Item):

    title = scrapy.Field()
    price = scrapy.Field()
    link = scrapy.Field()
    img = scrapy.Field()
    image = scrapy.Field()
    sku = scrapy.Field()
    unitprice = scrapy.Field()
    was_price = scrapy.Field()
    prod_count = scrapy.Field()
    rating = scrapy.Field()
    ProductRating = scrapy.Field()
    ProductTotalRatings = scrapy.Field()
    multiimages = scrapy.Field()
    brand = scrapy.Field()
    qty = scrapy.Field()
    is_available = scrapy.Field()
    variant = scrapy.Field()

    cat_id = scrapy.Field()
    category_name = scrapy.Field()
    category_url = scrapy.Field()
    currentversion = scrapy.Field()
    site_id = scrapy.Field()
    site_code = scrapy.Field()
    usdequal = scrapy.Field()
    usprice = scrapy.Field()
    category_table = scrapy.Field()

    product_id = scrapy.Field()
    product_url = scrapy.Field()
    description = scrapy.Field()
    brand = scrapy.Field()
    ProductCodeName = scrapy.Field()
    ProductCodevalue = scrapy.Field()
    volume = scrapy.Field()
    rating = scrapy.Field()
    product_rating = scrapy.Field()
    ProductRating = scrapy.Field()
    product_table = scrapy.Field()
    product_total_ratings = scrapy.Field()
    ingredients = scrapy.Field()
    ingredientsplaintext = scrapy.Field()
    nutrition = scrapy.Field()
    nutritionplaintext = scrapy.Field()
    multiimage_url = scrapy.Field()


class ProductDetailsItem(scrapy.Item):

    product_id = scrapy.Field()
    product_url = scrapy.Field()
    currentversion = scrapy.Field()
    site_code = scrapy.Field()
    description = scrapy.Field()
    brand = scrapy.Field()
    rating = scrapy.Field()
    product_rating = scrapy.Field()
    ProductRating = scrapy.Field()
    product_table = scrapy.Field()
    product_total_ratings = scrapy.Field()
    ingredients = scrapy.Field()
    ingredientsplaintext = scrapy.Field()
    nutrition = scrapy.Field()
    nutritionplaintext = scrapy.Field()
    multiimage_url = scrapy.Field()


class archivedetails(scrapy.Item):

    cat_id = scrapy.Field()
    site_code = scrapy.Field()
    category_url = scrapy.Field()
    category_table = scrapy.Field()
    currentversion = scrapy.Field()
