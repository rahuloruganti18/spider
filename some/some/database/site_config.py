from .db import get_connection

"""SITE_ID = 903

SITE_CODE = None
CATEGORY_TABLE = None
PRODUCT_TABLE = None
ARCHIVE_TABLE = None


def load_site_config():

    global SITE_CODE
    global CATEGORY_TABLE
    global PRODUCT_TABLE
    global ARCHIVE_TABLE

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("SELECT SiteCode FROM Sites WHERE Id = ?", (SITE_ID,))

        row = cursor.fetchone()

        if not row or not row[0]:
            raise Exception(f"SiteCode not found for Site ID {SITE_ID}")

        SITE_CODE = str(row[0]).strip()

        CATEGORY_TABLE = f"{SITE_CODE}_Categories"
        PRODUCT_TABLE = f"{SITE_CODE}_Products"
        ARCHIVE_TABLE = f"{SITE_CODE}_Products_Archive"

        # print("SITE ID       :", SITE_ID)
        # print("SITE CODE     :", SITE_CODE)
        # print("CATEGORY TABLE:", CATEGORY_TABLE)
        # print("PRODUCT TABLE :", PRODUCT_TABLE)
        # print("ARCHIVE TABLE :", ARCHIVE_TABLE)

    finally:

        cursor.close()
        connection.close()"""


def get_site_config(site_id):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("SELECT SiteCode FROM Sites WHERE Id = ?", (site_id,))

        row = cursor.fetchone()

        if not row or not row[0]:
            raise Exception(f"SiteCode not found for Site ID {site_id}")

        site_code = str(row[0]).strip()

        return {
            "site_id": site_id,
            "site_code": site_code,
            "category_table": f"{site_code}_Categories",
            "product_table": f"{site_code}_Products",
            "archive_table": f"{site_code}_Products_Archive",
        }

    finally:

        cursor.close()
        connection.close()


def get_conversion_rate(site_code):

    connection = get_connection()
    cursor = connection.cursor()

    try:
        qry = """
            SELECT ROUND(ConversionRate, 4) AS crate
            FROM Sites WITH (NOLOCK)
            WHERE SiteCode = ?
        """

        cursor.execute(qry, (site_code,))
        row = cursor.fetchone()

        return row.crate if row else None

    finally:
        cursor.close()
        connection.close()
