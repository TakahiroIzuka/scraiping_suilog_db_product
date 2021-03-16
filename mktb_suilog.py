from __future__ import print_function

import mysql.connector as mysql
from mysql.connector import errorcode

user_name = "admin"
password = "suilog_pass"
host = "db"  # docker-composeで定義したMySQLのサービス名
database_name = "suilog_db"

conn = mysql.connect(
    host="db",
    user="admin",
    passwd="suilogpass",
    port=3306,
    database="suilog_db"
)

cursor = conn.cursor()

DB_NAME = 'suilog_db'

TABLES = {}

TABLES['stores'] = (
    "CREATE TABLE stores ("
    "  `id` int(11) NOT NULL AUTO_INCREMENT,"
    "  `name` varchar(255) NOT NULL,"
    "  `type` varchar(16) NOT NULL,"
    "  `score` varchar(5) NOT NULL,"
    "  `smoking` varchar(255) NOT NULL,"
    "  `address` varchar(255) NOT NULL,"
    "  `ward` varchar(5) NOT NULL,"
    "  `station` varchar(255) NOT NULL,"
    "  `status` int(1) NOT NULL DEFAULT 1,"
    "  PRIMARY KEY (`id`)"
    ") ENGINE=InnoDB")

TABLES['urls'] = (
    "CREATE TABLE urls ("
    "  `store_id` int(11) NOT NULL AUTO_INCREMENT,"
    "  `url` varchar(255) NOT NULL,"
    "  PRIMARY KEY (`store_id`)"
    ") ENGINE=InnoDB")

TABLES['geos'] = (
    "CREATE TABLE geos ("
    "  `store_id` int(11) NOT NULL AUTO_INCREMENT,"
    "  `lat` double(8,6) NOT NULL,"
    "  `lng` double(9,6) NOT NULL,"
    "  PRIMARY KEY (`store_id`)"
    ") ENGINE=InnoDB")


  
def create_database(cursor):
    try:
        cursor.execute(
            "CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(DB_NAME))
    except mysql.Error as err:
        print("Failed creating database: {}".format(err))
        exit(1)

try:
    cursor.execute("USE {}".format(DB_NAME))
except mysql.Error as err:
    print("Database {} does not exists.".format(DB_NAME))
    if err.errno == errorcode.ER_BAD_DB_ERROR:
        create_database(cursor)
        print("Database {} created successfully.".format(DB_NAME))
        conn.database = DB_NAME
    else:
        print(err)
        exit(1)
for table_name in TABLES:
    table_description = TABLES[table_name]
    try:
        print("Creating table {}: ".format(table_name), end='')
        cursor.execute(table_description)
    except mysql.Error as err:
        if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
            print("already exists.")
        else:
            print(err.msg)
    else:
        print("OK")

cursor.close()
conn.close()