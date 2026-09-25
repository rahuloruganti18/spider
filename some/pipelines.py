import sys
import pyodbc
import datetime
from itemadapter import ItemAdapter
from .items import CategoryItem, CategoryDetailsItem, ProductItem, ProductDetailsItem
from scrapy.exceptions import CloseSpider
from .database.db import get_connection

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

        match item:
            case CategoryItem():
                return self.process_category(item, spider)
            case CategoryDetailsItem():
                return self.process_category_details(item, spider)
            case ProductItem():
                return self.process_product(item, spider)
            case ProductDetailsItem():
                return self.process_product_details(item, spider)
            case _:
                return item

    # =========================================================

    # CATEGORY PROCESSING
    # =========================================================
    def process_category(self, item, spider):

        category_table = item["category_table"]

        # site_id = item["site_id"]

        # site_code = item["site_code"]

        main_category_name = item["category_name"]

        main_category_url = item["category_url"]

        main_parent_id = item.get("parent_id", 0)

        # ------------------------------------------------------
        # INSERT MAIN CATEGORY
        # ------------------------------------------------------

        print()
        print("============================================")
        print("INSERTING MAIN CATEGORY")
        print("NAME:", main_category_name)
        print("URL:", main_category_url)
        print("PARENT ID:", main_parent_id)
        print(" category_table:", category_table)
        print("============================================")
        # exit()

        main_category_id = self.insert_category(
            category_table=category_table,
            category_name=main_category_name,
            category_url=main_category_url,
            parent_id=main_parent_id,
            # site_id=site_id,
            # site_code=site_code,
        )

        print("MAIN CATEGORY ID:", main_category_id, flush=True)

        if not main_category_id:

            print("MAIN CATEGORY INSERT FAILED:", main_category_name, flush=True)

            return item

        # ------------------------------------------------------
        # INSERT SUBCATEGORIES
        # ------------------------------------------------------

        subcategories = item.get("subcategories", [])

        for subcategory in subcategories:

            sub_category_name = subcategory["category_name"]

            sub_category_url = subcategory["category_url"]

            print()
            print("============================================")
            print("INSERTING SUB CATEGORY")
            print("NAME:", sub_category_name)
            print("URL:", sub_category_url)

            # IMPORTANT:
            # Main SubCategoryID becomes
            # Subcategory ParentCategoryID
            # ================================================

            sub_category_id = self.insert_category(
                category_table=category_table,
                category_name=sub_category_name,
                category_url=sub_category_url,
                parent_id=main_category_id,
                # site_id=site_id,
                # site_code=site_code,
            )

            print("SUB CATEGORY ID:", sub_category_id, flush=True)

            if not sub_category_id:

                print("SUB CATEGORY INSERT FAILED:", sub_category_name, flush=True)

                continue

            # --------------------------------------------------
            # INSERT SUB-SUB CATEGORIES
            # --------------------------------------------------

            sub_subcategories = subcategory.get("subcategories", [])

            for sub_subcategory in sub_subcategories:

                sub_sub_category_name = sub_subcategory["category_name"]

                sub_sub_category_url = sub_subcategory["category_url"]

                print()
                print("  ------------------------------------------")
                print("  INSERTING SUB-SUB CATEGORY")
                print("  NAME:", sub_sub_category_name)
                print("  URL:", sub_sub_category_url)

                # IMPORTANT:
                # Subcategory SubCategoryID becomes
                # Sub-subcategory ParentCategoryID
                # ================================================

                sub_sub_category_id = self.insert_category(
                    category_table=category_table,
                    category_name=sub_sub_category_name,
                    category_url=sub_sub_category_url,
                    parent_id=sub_category_id,
                    # site_id=site_id,
                    # site_code=site_code,
                )

                print("  SUB-SUB CATEGORY ID:", sub_sub_category_id, flush=True)

        print()
        print("CATEGORY PROCESS COMPLETED:", main_category_name, flush=True)

        return item

    # ==========================================================
    # INSERT CATEGORY
    # ==========================================================

    def insert_category(self, category_table, category_name, category_url, parent_id):

        try:

            # --------------------------------------------------
            # IMPORTANT
            #
            # category_table comes from your own code/database.
            # Do NOT put ? around table name.
            # --------------------------------------------------

            query = f"""
                INSERT INTO {category_table}
                (
                    SubCategoryName,
                    SubCategoryURL,
                    ParentCategoryID
                )
                OUTPUT INSERTED.SubCategoryID
                VALUES (?, ?, ?)
            """

            self.cursor.execute(query, (category_name, category_url, parent_id))

            # --------------------------------------------------
            # GET AUTO-INCREMENT CategoryID
            # --------------------------------------------------

            row = self.cursor.fetchone()

            if not row:

                self.connection.rollback()

                print("NO CATEGORY ID RETURNED:", category_name, flush=True)

                return None

            category_id = row[0]

            # --------------------------------------------------
            # COMMIT
            # --------------------------------------------------

            self.connection.commit()

            return category_id

        except Exception as e:

            self.connection.rollback()

            print()
            print("CATEGORY INSERT ERROR")
            print("NAME:", category_name)
            print("URL:", category_url)
            print("PARENT ID:", parent_id)
            print("ERROR:", e)
            print()

            return None

    # ==========================================================
    # CLOSE SPIDER
    # ==========================================================

    def close_spider(self, spider):

        print()
        print("############################################")
        print("PIPELINE CLOSE")
        print("############################################")

        try:

            if hasattr(self, "cursor"):

                self.cursor.close()

            if hasattr(self, "connection"):

                self.connection.close()

            print("DATABASE CLOSED", flush=True)

        except Exception as e:

            print("DATABASE CLOSE ERROR:", e, flush=True)

    def process_category_details(self, item, spider):

        cat_id = item.get("cat_id")
        category_url = item.get("category_url")
        category_table = item.get("category_table")
        currentversion = item.get("currentversion")
        product_count = item.get("product_count")

        print()
        print("######## PROCESS CATEGORY DETAILS ########", flush=True)

        print("CAT ID:", cat_id, flush=True)
        print("CATEGORY URL:", category_url, flush=True)
        print("CATEGORY TABLE:", category_table, flush=True)
        print("CURRENT VERSION:", currentversion, flush=True)
        print("PRODUCT COUNT:", product_count, flush=True)

        # --------------------------------------------------------
        # CHECK REQUIRED VALUES
        # --------------------------------------------------------

        if not category_table:
            print("######## CATEGORY TABLE MISSING ########", flush=True)
            return item

        if not category_url:
            print("######## CATEGORY URL MISSING ########", flush=True)
            return item

        # --------------------------------------------------------
        # UPDATE CATEGORY
        # --------------------------------------------------------

        query = f"""
            UPDATE {category_table}
            SET
                CurrentVersion = ?,
                ActualProductCount = ?
            WHERE SubCategoryURL = ?
        """

        values = (
            currentversion,
            product_count,
            category_url,
        )

        print("CATEGORY UPDATE QUERY:", query, flush=True)
        print("CATEGORY UPDATE VALUES:", values, flush=True)

        try:

            self.cursor.execute(query, values)

            self.connection.commit()

            print(
                f"######## CATEGORY UPDATED ######## "
                f"{cat_id} | {product_count} PRODUCTS",
                flush=True,
            )

        except Exception as e:

            self.connection.rollback()

            print("######## CATEGORY UPDATE ERROR ########", flush=True)

            print("CAT ID:", cat_id, flush=True)
            print("ERROR:", e, flush=True)

        return item

    # =========================================================
    # PRODUCT PROCESSING
    # =========================================================
    def process_product(self, item, spider):

        data = ItemAdapter(item)

        # ============================================================
        # GET VALUES FROM SCRAPED ITEM
        # ============================================================

        title = item.get("title")
        price = item.get("price")
        link = item.get("link")
        img = item.get("img")
        sku = item.get("sku")
        unitprice = item.get("unitprice")
        rating = item.get("rating")
        ProductRating = item.get("ProductRating")
        ProductTotalRatings = item.get("ProductTotalRatings")
        multiimages = item.get("multiimages")
        brand = item.get("brand")
        volume = item.get("volume")
        is_available = item.get("is_available")

        # These need to come from your spider/meta/calculation logic
        cat_id = item.get("cat_id")
        desc = item.get("desc")
        old_price = item.get("was_price")
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
                    qry = f"INSERT INTO {products_table} (CategoryID, PriceICCategoryID, Title, Description, ProductURL, OfferPrice, RegularPrice, USDPrice, ImageURL, SKU, Version, IsNew, price_range, categoryname, CCategoryName, UnitPrice, QuantityPrices, ProductCodeName, ProductCodevalue, FirstCrawledDate, FirstCrawledVersion, QTY, Brand, rating, ProductRating, ProductTotalRatings, MultiImage_Url, Availability) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?, ?, ?, ?, ?)"

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
                        unitprice,
                        ProductCodeName,
                        sku,
                        datetime.datetime.now(),
                        currentversion,
                        qty,
                        brand,
                        rating,
                        ProductRating,
                        ProductTotalRatings,
                        multiimages,
                        is_available,
                    )

                else:

                    qry = f"INSERT INTO {products_table} (CategoryID, Title, Description, ProductURL, OfferPrice, RegularPrice, USDPrice, ImageURL, SKU, Version, IsNew, price_range, categoryname, UnitPrice, QuantityPrices, ProductCodeName, ProductCodevalue, FirstCrawledDate, FirstCrawledVersion, QTY, Brand, rating, ProductRating, ProductTotalRatings, MultiImage_Url, qty, Availability) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"

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
                        unitprice,
                        ProductCodeName,
                        sku,
                        datetime.datetime.now(),
                        currentversion,
                        qty,
                        brand,
                        rating,
                        ProductRating,
                        ProductTotalRatings,
                        multiimages,
                        is_available,
                    )

                try:
                    self.cursor.execute(qry, values)
                    self.connection.commit()
                    print(f"INSERT: {sku}")

                except Exception as e:

                    self.connection.rollback()
                    print(f"Insert failed: {sku} | {e}")
                    exit()

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

    def process_product_details(self, item, spider):

        product_id = item.get("product_id")
        product_table = item.get("product_table")

        description = item.get("description")
        ingredients = item.get("ingredients")
        nutrition = item.get("nutrition")
        brand = item.get("brand")
        rating = item.get("rating")
        ProductRating = item.get("ProductRating")
        product_total_ratings = item.get("product_total_ratings")
        multiimage_url = item.get("multiimage_url")

        print()
        print("UPDATING PRODUCT:", product_id, flush=True)

        # =================================================
        # BUILD UPDATE DYNAMICALLY
        # =================================================

        update_columns = []
        update_values = []

        # Description
        if description is not None and str(description).strip() != "":
            update_columns.append("Description = ?")
            update_values.append(description)

        # Ingredients
        if ingredients is not None and str(ingredients).strip() != "":
            update_columns.append("Ingredients = ?")
            update_values.append(ingredients)

        # Nutrition
        if nutrition is not None and str(nutrition).strip() != "":
            update_columns.append("Nutrition = ?")
            update_values.append(nutrition)

        # Brand
        if brand is not None and str(brand).strip() != "":
            update_columns.append("Brand = ?")
            update_values.append(brand)

        # Rating
        if rating is not None and str(rating).strip() != "":
            update_columns.append("Rating = ?")
            update_values.append(rating)

            # ProductRating uses the same rating value
            update_columns.append("ProductRating = ?")
            update_values.append(rating)

        # ProductTotalRatings
        if (
            product_total_ratings is not None
            and str(product_total_ratings).strip() != ""
        ):
            update_columns.append("ProductTotalRatings = ?")
            update_values.append(product_total_ratings)

        # MultiImage_Url
        if multiimage_url is not None and str(multiimage_url).strip() != "":
            update_columns.append("MultiImage_Url = ?")
            update_values.append(multiimage_url)

        # =================================================
        # NOTHING TO UPDATE
        # =================================================

        if not update_columns:
            print(
                "######## NO PRODUCT DETAILS TO UPDATE ########",
                product_id,
                flush=True,
            )
            return item

        # =================================================
        # UPDATE QUERY
        # =================================================

        query = f"""
            UPDATE {product_table}
            SET {", ".join(update_columns)}
            WHERE ProductId = ?
        """

        update_values.append(product_id)

        print("UPDATE QUERY:", query, flush=True)
        print("UPDATE VALUES:", update_values, flush=True)

        # =================================================
        # EXECUTE UPDATE
        # =================================================

        try:

            self.cursor.execute(query, tuple(update_values))

            self.connection.commit()

            print(
                "######## PRODUCT UPDATED ########",
                product_id,
                flush=True,
            )

        except Exception as e:

            self.connection.rollback()

            print(
                "######## PRODUCT UPDATE ERROR ########",
                flush=True,
            )

            print("PRODUCT ID:", product_id, flush=True)
            print("ERROR:", e, flush=True)

        return item

    def close_spider(self, spider):

        try:

            if self.cursor:

                self.cursor.close()

            if self.connection:

                self.connection.close()

            print("######## DATABASE CONNECTION CLOSED ########", flush=True)

        except Exception as e:

            print("DATABASE CLOSE ERROR:", e, flush=True)
