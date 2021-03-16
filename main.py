import mysql.connector as mysql

conn = mysql.connect(
    host="db", # docker-composeで定義したMySQLのサービス名
    user="admin",
    passwd="suilogpass",
    port=3306,
    database="suilog_db"
)

conn.ping(reconnect=True)

print(conn.is_connected())
