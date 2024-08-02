import pymysql


def create_connection():
    try:
        connection = pymysql.connect(
            host='localhost',
            port=3306,
            database='',  # 数据库名称
            user='',  # 数据库用户名
            password=''  # 数据库密码
        )
        return connection
    except pymysql.MySQLError as e:
        print(f"Error: {e}")
        return None


def insert_model_data(connection, folder_name, model_name, image_url, category):
    insert_query = """
    INSERT INTO models (folder_name, model_name, image_url, category)
    VALUES (%s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
    image_url = VALUES(image_url),
    last_updated = CURRENT_TIMESTAMP
    """
    cursor = connection.cursor()
    cursor.execute(insert_query, (folder_name, model_name, image_url, category))
    connection.commit()


def fetch_model_data(connection, category):
    fetch_query = "SELECT folder_name, model_name, image_url, last_updated FROM models WHERE category = %s"
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    cursor.execute(fetch_query, (category,))
    rows = cursor.fetchall()
    return rows


# 从数据库中检索模型信息
def get_model_info(connection, sd_model_checkpoint):
    with connection.cursor() as cursor:
        sql = "SELECT * FROM model_db WHERE checkpoint = %s"
        cursor.execute(sql, (sd_model_checkpoint,))
        result = cursor.fetchone()
    return result