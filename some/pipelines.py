import sys
import pyodbc
import datetime
import os
import re
from itemadapter import ItemAdapter
from .items import (
    CategoryItem,
    CategoryDetailsItem,
    ProductItem,
    ProductDetailsItem,
    archivedetails,
)
from scrapy.exceptions import CloseSpider
from .database.db import get_connection

print("######## PIPELINES FILE LOADED ########")


class DatabasePipeline:

    def open_spider(self, spider):

        self.connection = get_connection()
        self.cursor = self.connection.cursor()

        self.site_code = None
        self.currentversion = None
        self.archive_required = False

        # self.sitecode = spider.site_code

        self.site_code = getattr(spider, "site_code", None)

        now = datetime.datetime.now()
        log_date = now.strftime("%Y-%m-%d")

        if self.site_code:

            log_dir = rf"C:\Logs\{self.site_code}"

            os.makedirs(log_dir, exist_ok=True)

            self.log_file_path = os.path.join(
                log_dir, f"product_update_errors_{log_date}.log"
            )

            print("SITE CODE:", self.site_code, flush=True)
            print("LOG FILE:", self.log_file_path, flush=True)

        else:
            now = datetime.datetime.now()
            log_date = now.strftime("%Y-%m-%d")
            log_dir = r"C:\Logs\{site_code}"
            os.makedirs(log_dir, exist_ok=True)

            self.log_file_path = os.path.join(
                log_dir, f"product_update_errors_{log_date}.log"
            )

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
            # case archivedetails():
            #     return self.archive_details(item, spider)
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

            sub_category_name = subcategory["sub_category_name"]

            sub_category_url = subcategory["sub_category_url"]

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

            sub_subcategories = subcategory.get("sub_subcategories", [])

            for sub_subcategory in sub_subcategories:

                sub_sub_category_name = sub_subcategory["sub_sub_category_name"]

                sub_sub_category_url = sub_subcategory["sub_sub_category_url"]

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

            now = datetime.datetime.now()
            error_time = now.strftime("%Y-%m-%d %H:%M:%S")
            error_message = f"[{error_time}] " f"CATEGORY INSERT ERROR : {str(e)}"

            with open(self.log_file_path, "a", encoding="utf-8") as log_file:

                log_file.write(error_message + "\n")

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

        # print("CATEGORY UPDATE QUERY:", query, flush=True)
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
            now = datetime.datetime.now()
            error_time = now.strftime("%Y-%m-%d %H:%M:%S")
            error_message = f"[{error_time}] " f"CATEGORY UPDATE ERROR : {str(e)}"

            with open(self.log_file_path, "a", encoding="utf-8") as log_file:

                log_file.write(error_message + "\n")

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
        image = item.get("image")
        sku = item.get("sku")
        ProductCodevalue = item.get("ProductCodevalue")
        if not ProductCodevalue or not ProductCodevalue.strip():
            ProductCodevalue = sku
        unitprice = item.get("unitprice")
        rating = item.get("rating")
        ProductRating = item.get("ProductRating")
        ProductRating = item.get("product_rating")
        ProductTotalRatings = item.get("ProductTotalRatings")
        ProductTotalRatings = item.get("product_total_ratings")
        multiimages = item.get("multiimages")
        brand = item.get("brand")
        volume = item.get("volume")
        is_available = item.get("is_available")
        variant = item.get("variant")

        # These need to come from your spider/meta/calculation logic
        cat_id = item.get("cat_id")
        description = item.get("description")
        ingredients = item.get("ingredients")
        old_price = item.get("was_price")
        usprice = item.get("usprice")
        genprice = item.get("genprice")
        gencatname = item.get("gencatname")
        unitprice = item.get("unitprice")
        qty = item.get("qty")
        ProductCodeName = item.get("ProductCodeName")
        brand = item.get("brand")

        currentversion = item.get("currentversion")
        site_id = item.get("site_id")
        site_code = item.get("site_code")
        usdequal = item.get("usdequal")
        category_name = item.get("category_name")
        genprice = price
        price = re.sub(r"[^\d.]", "", price)

        # if item.get("site_code"):
        #     self.site_code = item.get("site_code")

        # if item.get("currentversion") is not None:
        #     self.currentversion = item.get("currentversion")

        # site_code = response.meta.get("site_code")
        # currentversion = response.meta.get("currentversion")

        self.site_code = site_code
        self.currentversion = currentversion
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
                now = datetime.datetime.now()
                error_time = now.strftime("%Y-%m-%d %H:%M:%S")
                error_message = (
                    f"[{error_time}] " f"Database query error occurred : {str(e)}"
                )

                with open(self.log_file_path, "a", encoding="utf-8") as log_file:

                    log_file.write(error_message + "\n")

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

                now = datetime.datetime.now()
                error_time = now.strftime("%Y-%m-%d %H:%M:%S")
                error_message = (
                    f"[{error_time}] " f"Common category query error : {str(e)}"
                )

                with open(self.log_file_path, "a", encoding="utf-8") as log_file:

                    log_file.write(error_message + "\n")

            if commincatarr:
                catname = str(commincatarr.Name)

            # ========================================================
            # INSERT NEW PRODUCT
            # ========================================================

            if rowv is None or rowv[0] is None:

                qry = f"""
                    INSERT INTO {products_table} (CategoryID, PriceICCategoryID, Title, Description, ProductURL, OfferPrice, RegularPrice, USDPrice, ImageURL, SKU, Version, IsNew, price_range, categoryname, CCategoryName, UnitPrice, variant,  QuantityPrices, ProductCodeName, ProductCodevalue, FirstCrawledDate, FirstCrawledVersion, qty, Brand, rating, ProductRating, ProductTotalRatings, Availability, Ingredients, MultiImage_Url) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""

                values = (
                    cat_id,
                    commincatarr.TaxonomyNodeId if catname else None,
                    title,
                    description,
                    link,
                    price,
                    old_price,
                    usprice,
                    image,
                    sku,
                    currentversion,
                    1,
                    genprice,
                    category_name,
                    catname if catname else None,
                    unitprice,
                    variant,
                    unitprice,
                    ProductCodeName,
                    ProductCodevalue,
                    datetime.datetime.now(),
                    currentversion,
                    qty,
                    brand,
                    rating,
                    ProductRating,
                    ProductTotalRatings,
                    is_available,
                    ingredients,
                    multiimages,
                )

                try:
                    self.cursor.execute(qry, values)
                    self.connection.commit()
                    print(f"INSERT: {sku}")

                    now = datetime.datetime.now()
                    error_time = now.strftime("%Y-%m-%d %H:%M:%S")
                    error_message = f"[{error_time}] " f"INSERTED SKU: {sku}"

                    with open(self.log_file_path, "a", encoding="utf-8") as log_file:

                        log_file.write(error_message + "\n")

                except Exception as e:

                    self.connection.rollback()
                    print(f"Insert failed: {sku} | {e}")

                    now = datetime.datetime.now()
                    error_time = now.strftime("%Y-%m-%d %H:%M:%S")
                    error_message = (
                        f"[{error_time}] "
                        f"INSERT Failed SKU: {sku} | "
                        f"URL: {link} | "
                        f"ERROR: {str(e)}"
                    )

                    with open(self.log_file_path, "a", encoding="utf-8") as log_file:

                        log_file.write(error_message + "\n")

            # ========================================================
            # UPDATE EXISTING PRODUCT
            # ========================================================

            else:

                existing_version = rowv[0]
                if existing_version < currentversion:
                    qry = f"""UPDATE {products_table} SET OfferPrice = ?, RegularPrice = ?, USDPrice = ?, ImageURL = ?, RecordDate = ?, Version = ?, IsNew = 0, price_range = ?, categoryname = ?, CCategoryName = ?, UnitPrice = ?, QuantityPrices = ?  WHERE SKU = ?"""

                    values = (
                        price,
                        old_price,
                        usprice,
                        image,
                        datetime.datetime.now(),
                        currentversion,
                        genprice,
                        category_name,
                        catname if catname else None,
                        unitprice,
                        qty,
                        sku,
                    )

                    try:

                        self.cursor.execute(qry, values)
                        self.connection.commit()
                        print(f"UPDATE: {sku}")

                    except Exception as e:

                        self.connection.rollback()
                        print(f"Update failed: {sku} | {e}")

                        now = datetime.datetime.now()
                        error_time = now.strftime("%Y-%m-%d %H:%M:%S")
                        error_message = (
                            f"[{error_time}] "
                            f"UPDATE Failed SKU: {sku} | "
                            f"ERROR: {str(e)}"
                        )

                        with open(
                            self.log_file_path, "a", encoding="utf-8"
                        ) as log_file:

                            log_file.write(error_message + "\n")

                # ====================================================
                # SAME VERSION
                # ====================================================

                elif existing_version == currentversion:

                    print(f"Already exists: {sku}")

                    now = datetime.datetime.now()
                    error_time = now.strftime("%Y-%m-%d %H:%M:%S")
                    error_message = f"[{error_time}] " f"ALREADY EXISTS : {sku}"

                    with open(self.log_file_path, "a", encoding="utf-8") as log_file:

                        log_file.write(error_message + "\n")

            # self.archive_required = True

        except Exception as e:

            print(f"Product processing error: {e}")

        return item

    def close_spider(self, spider):

        try:
            print("######## PRODUCT SPIDER CLOSING ########", flush=True)
            print(f"SITE CODE: {self.site_code}", flush=True)
            print(f"CURRENT VERSION: {self.currentversion}", flush=True)

            self.archive_details()

        except Exception as e:
            print(f"CLOSE SPIDER ERROR: {e}", flush=True)

        finally:

            if self.cursor:
                self.cursor.close()

            if self.connection:
                self.connection.close()

            print("######## DATABASE CONNECTION CLOSED ########", flush=True)

    def process_product_details(self, item, spider):

        product_id = item.get("product_id")
        product_table = item.get("product_table")
        site_code = item.get("site_code")
        currentversion = item.get("currentversion")

        self.site_code = site_code
        self.currentversion = currentversion

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

            now = datetime.datetime.now()
            error_time = now.strftime("%Y-%m-%d %H:%M:%S")
            error_message = (
                f"[{error_time}] " f"PRODUCT ID: {product_id} | " f"ERROR: {str(e)}"
            )

            print(
                "######## PRODUCT UPDATE ERROR ########",
                flush=True,
            )

            print(
                error_message,
                flush=True,
            )

            with open(self.log_file_path, "a", encoding="utf-8") as log_file:

                log_file.write(error_message + "\n")

        self.archive_required = True

        return item

    def close_spider(self, spider):

        try:
            print("######## PRODUCT DETAILS SPIDER CLOSING ########", flush=True)

            print(f"SITE CODE: {self.site_code}", flush=True)
            print(f"CURRENT VERSION: {self.currentversion}", flush=True)
            print(f"ARCHIVE REQIRED: {self.archive_required}", flush=True)

            if self.archive_required:
                self.archive_details(self, spider)

        except Exception as e:
            print(f"CLOSE SPIDER ERROR: {e}", flush=True)

        finally:

            if self.cursor:
                self.cursor.close()

            if self.connection:
                self.connection.close()

            print("######## DATABASE CONNECTION CLOSED ########", flush=True)

        # try:

        #     if self.cursor:
        #         self.cursor.close()

        #     if self.connection:
        #         self.connection.close()

        #     print("######## DATABASE CONNECTION CLOSED ########", flush=True)

        # except Exception as e:

        #     print("DATABASE CLOSE ERROR:", e, flush=True)

    def archive_details(self, item, spider):

        try:
            site_code = self.site_code
            currentversion = self.currentversion

            products_table = f"{site_code}_Products"
            native_table = f"{site_code}_Products_Native"
            archive_table = f"{site_code}_Products_Archive"

            # Get IsEnglish and SiteName
            self.cursor.execute(
                "SELECT isenglish, SiteName FROM Sites WITH (NOLOCK) WHERE SiteCode = ?",
                (site_code,),
            )

            row = self.cursor.fetchone()

            is_english = row[0] if row else 1
            SiteName = row[1] if row else ""

            print(f"SITE CODE: {site_code}", flush=True)
            print(f"SITE NAME: {SiteName}", flush=True)
            print(f"IS ENGLISH: {is_english}", flush=True)
            print(f"CURRENT VERSION: {currentversion}", flush=True)

            now = datetime.datetime.now()
            error_time = now.strftime("%Y-%m-%d %H:%M:%S")
            error_message = (
                f"[{error_time}] "
                f"PRODUCT ID: {site_code} | "
                f"IS ENGLISH: {is_english} | "
                f"SITE NAME: {SiteName}| "
                f"CURRENT VERSION: {currentversion}"
            )

            with open(self.log_file_path, "a", encoding="utf-8") as log_file:

                log_file.write(error_message + "\n")

            # ==================================================
            # VERSION 1
            # ==================================================

            if currentversion == 1:

                # ==================================================
                # NATIVE - only when IsEnglish = 0
                # ==================================================

                if is_english == 0:

                    # ==================================================
                    # NATIVE - create table if it does not exist
                    # ==================================================

                    self.cursor.execute(
                        f"SELECT COUNT(*) "
                        f"FROM sys.tables "
                        f"WHERE name = '{native_table.split('.')[-1]}'"
                    )

                    table_exists = self.cursor.fetchone()[0]

                    # --------------------------------------------------
                    # Native table does not exist
                    # --------------------------------------------------

                    if table_exists == 0:

                        self.cursor.execute(
                            f"SELECT * INTO {native_table} " f"FROM {products_table}"
                        )

                    # --------------------------------------------------
                    # Native table already exists
                    # --------------------------------------------------

                    else:

                        self.cursor.execute(
                            f"INSERT INTO {native_table} "
                            f"SELECT * FROM {products_table}"
                        )

                    # --------------------------------------------------
                    # Get native count
                    # --------------------------------------------------

                    self.cursor.execute(f"SELECT COUNT(*) FROM {native_table}")

                    result = self.cursor.fetchone()

                    native_rows = result[0] if result else 0

                    print(f"NATIVE: {native_rows} products copied", flush=True)

                    self.connection.commit()

                    now = datetime.datetime.now()
                    error_time = now.strftime("%Y-%m-%d %H:%M:%S")
                    error_message = (
                        f"[{error_time}] " f"NATIVE: {native_rows} products copied"
                    )

                    with open(self.log_file_path, "a", encoding="utf-8") as log_file:

                        log_file.write(error_message + "\n")

                else:
                    print(f"IS ENGLISH = 1 -> NATIVE SKIPPED", flush=True)
                    now = datetime.datetime.now()
                    error_time = now.strftime("%Y-%m-%d %H:%M:%S")
                    error_message = (
                        f"[{error_time}] " f"IS ENGLISH = 1 -> NATIVE SKIPPED"
                    )

                    with open(self.log_file_path, "a", encoding="utf-8") as log_file:

                        log_file.write(error_message + "\n")

                # ==================================================
                # ARCHIVE - create table if it does not exist
                # ==================================================

                self.cursor.execute(
                    f"SELECT COUNT(*) "
                    f"FROM sys.tables "
                    f"WHERE name = '{archive_table.split('.')[-1]}'"
                )

                table_exists = self.cursor.fetchone()[0]

                # --------------------------------------------------
                # Archive table does not exist
                # --------------------------------------------------

                if table_exists == 0:

                    self.cursor.execute(
                        f"SELECT * INTO {archive_table} " f"FROM {products_table}"
                    )

                # --------------------------------------------------
                # Archive table already exists
                # --------------------------------------------------

                else:

                    self.cursor.execute(
                        f"INSERT INTO {archive_table} "
                        f"SELECT * FROM {products_table}"
                    )

                # --------------------------------------------------
                # Get archive count
                # --------------------------------------------------

                self.cursor.execute(f"SELECT COUNT(*) FROM {archive_table}")

                result = self.cursor.fetchone()

                rows_affected = result[0] if result else 0

                print(f"ARCHIVE: {rows_affected} products copied", flush=True)

                self.connection.commit()

                now = datetime.datetime.now()
                error_time = now.strftime("%Y-%m-%d %H:%M:%S")
                error_message = (
                    f"[{error_time}] " f"ARCHIVE: {rows_affected} products copied"
                )

                with open(self.log_file_path, "a", encoding="utf-8") as log_file:

                    log_file.write(error_message + "\n")
            else:

                # Native only when IsEnglish = 0
                if is_english == 0:

                    self.cursor.execute(f"SET IDENTITY_INSERT {native_table} ON")

                    native_query = f"INSERT INTO {native_table} (ProductId, CategoryID, PriceICCategoryID, Title, Description, Brand, USDPrice, OfferPrice, RegularPrice, SaveAmount, ShippingAmount, UPC, PrefixCode, ProductOrigin, ISBN, SKU, MPN, Availability, QuantityPrices, ProductURL, Features, Colors, RecordDate, ImageURL, Version, IsNew, price_range, categoryname, CCategoryName, UnitPrice, SpecialOffer) SELECT ProductId, CategoryID, PriceICCategoryID, Title, Description, Brand, USDPrice, OfferPrice, RegularPrice, SaveAmount, ShippingAmount, UPC, PrefixCode, ProductOrigin, ISBN, SKU, MPN, Availability, QuantityPrices, ProductURL, Features, Colors, RecordDate, ImageURL, Version, IsNew, price_range, categoryname, CCategoryName, UnitPrice, SpecialOffer FROM {products_table} WHERE Version = ? AND IsNew = 1"

                    self.cursor.execute(native_query, (currentversion,))

                    native_rows = self.cursor.rowcount

                    self.cursor.execute(f"SET IDENTITY_INSERT {native_table} OFF")

                    print(f"NATIVE: {native_rows} products copied", flush=True)

                    now = datetime.datetime.now()
                    error_time = now.strftime("%Y-%m-%d %H:%M:%S")
                    error_message = (
                        f"[{error_time}] " f"NATIVE: {native_rows} products copied"
                    )

                    with open(self.log_file_path, "a", encoding="utf-8") as log_file:

                        log_file.write(error_message + "\n")

                else:

                    print(f"IS ENGLISH = 1 -> NATIVE SKIPPED", flush=True)

                    now = datetime.datetime.now()
                    error_time = now.strftime("%Y-%m-%d %H:%M:%S")
                    error_message = (
                        f"[{error_time}] " f"IS ENGLISH = 1 -> NATIVE SKIPPED"
                    )

                    with open(self.log_file_path, "a", encoding="utf-8") as log_file:

                        log_file.write(error_message + "\n")

                # Archive always
                self.cursor.execute(f"SET IDENTITY_INSERT {archive_table} ON")

                archive_query = f"INSERT INTO {archive_table} (ProductId, CategoryID, PriceICCategoryID, Title, Description, Brand, USDPrice, OfferPrice, RegularPrice, SaveAmount, ShippingAmount, UPC, PrefixCode, ProductOrigin, ISBN, SKU, MPN, Availability, QuantityPrices, ProductURL, Features, Colors, RecordDate, ImageURL, Version, IsNew, price_range, categoryname, CCategoryName, unit, QTY_Extract, qty, ProductCodeName, ProductCodeValue) SELECT ProductId, CategoryID, PriceICCategoryID, Title, Description, Brand, USDPrice, OfferPrice, RegularPrice, SaveAmount, ShippingAmount, UPC, PrefixCode, ProductOrigin, ISBN, SKU, MPN, Availability, QuantityPrices, ProductURL, Features, Colors, RecordDate, ImageURL, Version, IsNew, price_range, categoryname, CCategoryName, unit, QTY_Extract, qty, ProductCodeName, ProductCodeValue FROM {products_table} WHERE Version = ? AND OfferPrice != ''"

                self.cursor.execute(archive_query, (currentversion,))

                rows_affected = self.cursor.rowcount

                self.cursor.execute(f"SET IDENTITY_INSERT {archive_table} OFF")

                print(f"ARCHIVE: {rows_affected} products copied", flush=True)

                now = datetime.datetime.now()
                error_time = now.strftime("%Y-%m-%d %H:%M:%S")
                error_message = (
                    f"[{error_time}] " f"ARCHIVE: {rows_affected} products copied"
                )

                with open(self.log_file_path, "a", encoding="utf-8") as log_file:

                    log_file.write(error_message + "\n")

            # ==================================================
            # PREVIOUS VERSION
            # ==================================================

            prevversion = currentversion - 1

            self.cursor.execute(
                "SELECT VersionCount FROM Sites_Download_History WITH (NOLOCK) WHERE SiteCode = ? AND Version = ?",
                (site_code, prevversion),
            )

            row2 = self.cursor.fetchone()

            prevcount = row2[0] if row2 else 0

            print(f"PREVIOUS VERSION COUNT: {prevcount}", flush=True)

            now = datetime.datetime.now()
            error_time = now.strftime("%Y-%m-%d %H:%M:%S")
            error_message = f"[{error_time}] " f"PREVIOUS VERSION COUNT: {prevcount}"

            with open(self.log_file_path, "a", encoding="utf-8") as log_file:

                log_file.write(error_message + "\n")

            query = f"""SELECT TOP 1 RecordDate FROM {products_table} WITH (NOLOCK) WHERE Version = ? ORDER BY RecordDate ASC"""

            self.cursor.execute(query, (currentversion))

            row = self.cursor.fetchone()

            if row:
                start_time = row[0]
            else:
                start_time = None

            print("START TIME:", start_time, flush=True)

            # ==================================================
            # DOWNLOAD HISTORY
            # ==================================================

            history_query = "INSERT INTO Sites_Download_History (Sitename, Sitecode, DownloadStart, DownloadEnd, Version, VersionCount, Resource) VALUES (?, ?, ?, ?, ?, ?, ?)"

            self.cursor.execute(
                history_query,
                (
                    SiteName,
                    site_code,
                    start_time,
                    datetime.datetime.now(),
                    currentversion,
                    rows_affected,
                    "Rahul",
                ),
            )

            self.connection.commit()

            print(f"HISTORY INSERTED: VersionCount = {rows_affected}", flush=True)

            print(f"ARCHIVE / NATIVE / HISTORY COMPLETED", flush=True)

            now = datetime.datetime.now()
            error_time = now.strftime("%Y-%m-%d %H:%M:%S")
            error_message = (
                f"[{error_time}] "
                f"HISTORY INSERTED: VersionCount = {rows_affected} | "
                f"ARCHIVE / NATIVE / HISTORY COMPLETED"
            )

            with open(self.log_file_path, "a", encoding="utf-8") as log_file:

                log_file.write(error_message + "\n")

        except Exception as e:

            self.connection.rollback()

            now = datetime.datetime.now()
            error_time = now.strftime("%Y-%m-%d %H:%M:%S")
            error_message = (
                f"[{error_time}] " f"ARCHIVE / NATIVE / HISTORY FAILED : {str(e)}"
            )

            with open(self.log_file_path, "a", encoding="utf-8") as log_file:

                log_file.write(error_message + "\n")

            print(f"ARCHIVE / NATIVE / HISTORY FAILED: {e}", flush=True)

            # Turn off IDENTITY_INSERT if an error occurs
            try:
                self.cursor.execute(f"SET IDENTITY_INSERT {native_table} OFF")
            except Exception:
                pass

            try:
                self.cursor.execute(f"SET IDENTITY_INSERT {archive_table} OFF")
            except Exception:
                pass

            raise
