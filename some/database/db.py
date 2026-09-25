import pyodbc
import sys
import requests
from base64 import b64decode

# Connection configuration
server = "10.8.196.155"
# database = "priceIC_Live_Archive"
database = "priceIC_Live"
username = "priceuser"
password = "pass@121"
zytekey = "a50e118938824ee7bc1fa1fd743357c0"


# Build connection string
def get_connection():
    try:
        conn = pyodbc.connect(
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
        )
        return conn
    except pyodbc.Error as e:
        print(f"Database connection failed: {e}")
        sys.exit(1)


def zyte(url):

    api_response = requests.post(
        "https://api.zyte.com/v1/extract",
        auth=(zytekey, ""),
        json={
            "url": url,
            "httpResponseBody": True,
        },
    )

    http_response_body: bytes = b64decode(api_response.json()["httpResponseBody"])
    res = http_response_body.decode("utf-8")
    return res
