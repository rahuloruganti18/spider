import sys
import pyodbc
import datetime
from itemadapter import ItemAdapter
from .items import CategoryItem, ProductItem
from scrapy.exceptions import CloseSpider

sys.path.insert(0, r"C:\Fullstock\Python")
from connections.dbconnect import get_connection

print("######## PIPELINES FILE LOADED ########")


class DatabasePipeline:

    def open_spider(self, spider):

        self.connection = get_connection()
        self.cursor = self.connection.cursor()

        print("######## DATABASE CONNECTED ########")

    def process_item(self, item, spider):

        # =====================================================
        # CATEGORY ITEM
        # =====================================================

        if isinstance(item, CategoryItem):

            return self.process_category(item, spider)

        # =====================================================
        # PRODUCT ITEM
        # =====================================================

        elif isinstance(item, ProductItem):

            return self.process_product(item, spider)

        return item

    # =========================================================

    # CATEGORY PROCESSING
    # =========================================================
    def process_category(self, item, spider):

        data = ItemAdapter(item)

        category_name = data["category_name"]

        category_url = data["category_url"]

        site_id = data["site_id"]

        site_code = data["site_code"]

        category_table = data["category_table"]

        parent_id = data["parent_id"]

        subcategories = data.get("subcategories", [])

        print()
        print("############################################", flush=True)

        print("PIPELINE CATEGORY:", category_name, flush=True)

        print("PIPELINE URL:", category_url, flush=True)

        print("PIPELINE PARENT ID:", parent_id, flush=True)

        print("SUB CATEGORY COUNT:", len(subcategories), flush=True)

        print("############################################", flush=True)

        # ======================================================
        # INSERT CATEGORY
        #
        # For MAIN:
        #
        # ParentCategoryID = 1
        #
        # For SUB-SUB:
        #
        # ParentCategoryID = SubCategoryID
        # ======================================================

        insert_sql = f"""
            INSERT INTO {category_table}
            (
                SubCategoryName,
                SubCategoryURL,
                ParentCategoryID
            )
            OUTPUT INSERTED.SubCategoryID
            VALUES (?, ?, ?)
        """

        values = (category_name, category_url, parent_id)

        print()
        print("######## INSERTING CATEGORY ########", flush=True)

        print("NAME:", category_name, flush=True)

        print("URL:", category_url, flush=True)

        print("PARENT ID:", parent_id, flush=True)

        self.cursor.execute(insert_sql, values)

        # ======================================================
        # GET INSERTED ID
        # ======================================================

        row = self.cursor.fetchone()

        if not row:

            raise Exception("Could not get inserted CategoryID: " + category_name)

        category_id = row[0]

        print()
        print("######## CATEGORY INSERTED ########", flush=True)

        print("CATEGORY:", category_name, flush=True)

        print("CATEGORY ID:", category_id, flush=True)

        self.connection.commit()

        # ======================================================
        # IMPORTANT
        #
        # If subcategories are present, this item is a
        # MAIN CATEGORY.
        #
        # category_id is therefore MAIN CATEGORY ID.
        #
        # Every subcategory gets:
        #
        # ParentCategoryID = category_id
        # ======================================================

        for sub in subcategories:

            sub_name = sub["name"]

            sub_url = sub["url"]

            print()
            print("------------------------------------------", flush=True)

            print("INSERTING SUB CATEGORY:", sub_name, flush=True)

            print("SUB URL:", sub_url, flush=True)

            print("SUB PARENT ID:", category_id, flush=True)

            print("------------------------------------------", flush=True)

            # ==================================================
            # INSERT SUB CATEGORY
            # ==================================================

            sub_insert_sql = f"""
                INSERT INTO {category_table}
                (
                    SubCategoryName,
                    SubCategoryURL,
                    ParentCategoryID
                )
                OUTPUT INSERTED.SubCategoryID
                VALUES (?, ?, ?)
            """

            sub_values = (sub_name, sub_url, category_id)

            self.cursor.execute(sub_insert_sql, sub_values)

            # ==================================================
            # GET SUB CATEGORY ID
            # ==================================================

            sub_row = self.cursor.fetchone()

            if not sub_row:

                raise Exception("Could not get SubCategoryID: " + sub_name)

            sub_category_id = sub_row[0]

            print()
            print("######## SUB CATEGORY INSERTED ########", flush=True)

            print("SUB CATEGORY:", sub_name, flush=True)

            print("SUB CATEGORY ID:", sub_category_id, flush=True)

            print("SUB PARENT ID:", category_id, flush=True)

            self.connection.commit()

            # ==================================================
            # OPEN SUB CATEGORY URL
            #
            # The sub_category_id is passed to the spider.
            #
            # Spider will use this ID as ParentCategoryID
            # for sub-sub categories.
            # ==================================================

            print()
            print("######## OPENING SUB CATEGORY URL ########", flush=True)

            print("SUB CATEGORY:", sub_name, flush=True)

            print("SUB URL:", sub_url, flush=True)

            print("SUB CATEGORY ID:", sub_category_id, flush=True)

            request = spider.make_subcategory_request(
                url=sub_url,
                sub_category_name=sub_name,
                sub_category_url=sub_url,
                sub_category_id=sub_category_id,
                site_id=site_id,
                site_code=site_code,
                category_table=category_table,
            )

            # ==================================================
            # SCHEDULE REQUEST
            # ==================================================

            spider.crawler.engine.crawl(request)

            print("######## SUB CATEGORY REQUEST SCHEDULED ########", flush=True)

        # ======================================================
        # RETURN ITEM
        # ======================================================

        return item

    # ==========================================================
    # CLOSE SPIDER
    # ==========================================================

    def close_spider(self, spider):

        print("######## CATEGORY PIPELINE CLOSE ########", flush=True)

        if hasattr(self, "cursor"):

            self.cursor.close()

        if hasattr(self, "connection"):

            self.connection.close()

        print("######## DATABASE CONNECTION CLOSED ########", flush=True)

    # =========================================================
    # PRODUCT PROCESSING
    # =========================================================
    def process_product(self, item, spider):

        data = ItemAdapter(item)

        """print("######## PROCESS ITEM ########")
        print("SKU:", item.get("sku"))
        print("TITLE:", item.get("title"))
        print("PRICE:", item.get("price"))
        print("CAT ID:", item.get("cat_id"))
        print("CURRENT VERSION:", item.get("currentversion"))
        print("SITE ID:", item.get("site_id"))

        print("######## PROCESS_ITEM CALLED ########")
        print("ITEM:", dict(item))

        return item"""

        # ============================================================
        # GET VALUES FROM SCRAPED ITEM
        # ============================================================

        title = item.get("title")
        price = item.get("price")
        link = item.get("link")
        img = item.get("img")
        sku = item.get("sku")

        # These need to come from your spider/meta/calculation logic
        cat_id = item.get("cat_id")
        desc = item.get("desc")
        old_price = item.get("old_price")
        usprice = item.get("usprice")
        genprice = item.get("genprice")
        gencatname = item.get("gencatname")
        unitprice = item.get("unitprice")
        qty = item.get("qty")
        ProductCodeName = "ItemNo"
        brand = item.get("brand")

        currentversion = item.get("currentversion")
        site_id = item.get("site_id")
        site_code = item.get("site_code")
        usdequal = item.get("usdequal")
        category_name = item.get("category_name")
        genprice = price
        try:
            usprice = round(float(usdequal) * float(price), 2)
        except (ValueError, TypeError):
            usprice = 0.0
        # ============================================================
        # CHECK TITLE / PRICE
        # ============================================================
        products_table = f"{site_code}_Products"

        if not title or not price:

            print("TITLE OR PRICE MISSING:", link)

            # Your old code:
            #
            # write_log(
            #     f"\n{link}",
            #     f"C:\\Logs\\BBWAU_titleNA_log_{logdt}.txt"
            # )

            return item

        try:

            # ========================================================
            # CHECK PRODUCT BY SKU
            # ========================================================

            rowv = None

            sel = f"SELECT Version FROM {products_table} WITH (NOLOCK) WHERE SKU = ?"

            try:
                self.cursor.execute(sel, (sku,))
                rowv = self.cursor.fetchone()

            except pyodbc.Error as e:
                print(f"Database query error occurred: {e}")
                return item

            # ========================================================
            # GET COMMON CATEGORY
            # ========================================================

            commincatarr = None
            catname = ""

            commincatqry = "SELECT TaxonomyNodeId, TaxonomyNode.Name FROM SiteTaxonomyNode INNER JOIN TaxonomyNode ON SiteTaxonomyNode.TaxonomyNodeId = TaxonomyNode.Id WHERE CategoryId = ? AND SiteId = ?"

            try:
                self.cursor.execute(commincatqry, (cat_id, site_id))
                commincatarr = self.cursor.fetchone()

            except pyodbc.Error as e:
                print(f"Common category query error: {e}")

            if commincatarr:
                catname = str(commincatarr.Name)

            # ========================================================
            # INSERT NEW PRODUCT
            # ========================================================

            if rowv is None or rowv[0] is None:

                if catname:
                    qry = f"INSERT INTO {products_table} (CategoryID, PriceICCategoryID, Title, Description, ProductURL, OfferPrice, RegularPrice, USDPrice, ImageURL, SKU, Version, IsNew, price_range, categoryname, CCategoryName, UnitPrice, QuantityPrices, ProductCodeName, ProductCodevalue, FirstCrawledDate, FirstCrawledVersion, QTY, Brand) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"

                    values = (
                        cat_id,
                        commincatarr.TaxonomyNodeId,
                        title,
                        desc,
                        link,
                        price,
                        old_price,
                        usprice,
                        img,
                        sku,
                        currentversion,
                        1,
                        genprice,
                        category_name,
                        catname,
                        unitprice,
                        qty,
                        ProductCodeName,
                        sku,
                        datetime.datetime.now(),
                        currentversion,
                        qty,
                        brand,
                    )

                else:

                    qry = f"INSERT INTO {products_table} (CategoryID, Title, Description, ProductURL, OfferPrice, RegularPrice, USDPrice, ImageURL, SKU, Version, IsNew, price_range, categoryname, UnitPrice, QuantityPrices, ProductCodeName, ProductCodevalue, FirstCrawledDate, FirstCrawledVersion, QTY, Brand) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"

                    values = (
                        cat_id,
                        title,
                        desc,
                        link,
                        price,
                        old_price,
                        usprice,
                        img,
                        sku,
                        currentversion,
                        1,
                        genprice,
                        category_name,
                        unitprice,
                        qty,
                        ProductCodeName,
                        sku,
                        datetime.datetime.now(),
                        currentversion,
                        qty,
                        brand,
                    )

                try:
                    self.cursor.execute(qry, values)
                    self.connection.commit()
                    print(f"INSERT: {sku}")

                except Exception as e:

                    self.connection.rollback()
                    print(f"Insert failed: {sku} | {e}")

            # ========================================================
            # UPDATE EXISTING PRODUCT
            # ========================================================

            else:

                existing_version = rowv[0]
                if existing_version < currentversion:
                    if catname:

                        qry = f"UPDATE {products_table} SET OfferPrice = ?, RegularPrice = ?, USDPrice = ?, ImageURL = ?, RecordDate = ?, Version = ?, IsNew = 0, price_range = ?, categoryname = ?, CCategoryName = ?, UnitPrice = ?, QuantityPrices = ?, Brand = ? WHERE SKU = ?"

                        values = (
                            price,
                            old_price,
                            usprice,
                            img,
                            datetime.datetime.now(),
                            currentversion,
                            genprice,
                            category_name,
                            catname,
                            unitprice,
                            qty,
                            brand,
                            sku,
                        )

                    else:

                        qry = f"UPDATE {products_table} SET OfferPrice = ?, RegularPrice = ?, USDPrice = ?, ImageURL = ?, RecordDate = ?, Version = ?, IsNew = 0, price_range = ?, categoryname = ?, UnitPrice = ?, QuantityPrices = ?, Brand = ? WHERE SKU = ?"

                        values = (
                            price,
                            old_price,
                            usprice,
                            img,
                            datetime.datetime.now(),
                            currentversion,
                            genprice,
                            category_name,
                            unitprice,
                            qty,
                            brand,
                            sku,
                        )

                    try:

                        self.cursor.execute(qry, values)
                        self.connection.commit()
                        print(f"UPDATE: {sku}")

                    except Exception as e:

                        self.connection.rollback()
                        print(f"Update failed: {sku} | {e}")

                # ====================================================
                # SAME VERSION
                # ====================================================

                elif existing_version == currentversion:

                    print(f"Already exists: {sku}")

        except Exception as e:

            print(f"Product processing error: {e}")

        return item

    def close_spider(self, spider):

        self.cursor.close()
        self.connection.close()

        print("######## DATABASE CONNECTION CLOSED ########")
