import os

import pymysql
from flask import jsonify

from func.database.azure.func import upload_to_azure


AZURE_EXPIRATION_HOURS = 1

def get_db_connection():
    return pymysql.connect(host='localhost', user='', password='', database='', charset='utf8mb4',
                           cursorclass=pymysql.cursors.DictCursor)

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

def transform_data(rows):
    data = {'folders': []}
    folder_dict = {}

    for row in rows:
        folder_name = row['folder_name']
        model_name = row['model_name']
        image_url = row['image_url']

        if folder_name not in folder_dict:
            folder_dict[folder_name] = {'name': folder_name, 'models': []}
            data['folders'].append(folder_dict[folder_name])

        folder_dict[folder_name]['models'].append({'name': model_name, 'image_path': image_url})

    return data

def handle_request(category, base_folder):
    connection = create_connection()
    if connection:
        check_and_upload_model(connection, base_folder, (".png", ".jpg", ".jpeg"), category)
        rows = fetch_model_data(connection, category)
        data = transform_data(rows)
        connection.close()
        return jsonify(data)
    else:
        return jsonify({"error": "Database connection failed"}), 500

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


# 从数据库中检索模型信息
def get_model_info(connection, sd_model_checkpoint):
    with connection.cursor() as cursor:
        sql = "SELECT * FROM model_db WHERE checkpoint = %s"
        cursor.execute(sql, (sd_model_checkpoint,))
        result = cursor.fetchone()
    return result


def check_and_upload_model(connection, base_folder, image_extensions, category):
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT model_name FROM models WHERE category = %s", (category,))
    existing_models = {row['model_name'] for row in cursor.fetchall()}

    seen_names = set()

    for item_name in os.listdir(base_folder):
        item_path = os.path.join(base_folder, item_name)
        if os.path.isdir(item_path):
            for filename in os.listdir(item_path):
                name_without_extension = os.path.splitext(filename)[0]
                if filename.endswith(image_extensions):
                    if name_without_extension in seen_names or name_without_extension in existing_models:
                        continue
                    model_name = name_without_extension
                    image_path = os.path.join(item_path, filename)
                    image_url = upload_to_azure(image_path, filename, AZURE_EXPIRATION_HOURS)
                    insert_model_data(connection, item_name, model_name, image_url, category)
                    seen_names.add(name_without_extension)
        else:
            name_without_extension = os.path.splitext(item_name)[0]
            if item_name.endswith(image_extensions):
                if name_without_extension in seen_names or name_without_extension in existing_models:
                    continue
                model_name = name_without_extension
                image_path = item_path
                image_url = upload_to_azure(image_path, item_name, AZURE_EXPIRATION_HOURS)
                insert_model_data(connection, '', model_name, image_url, category)
                seen_names.add(name_without_extension)


def get_models_and_folders(base_folder, image_extensions, category):
    folders = []
    files = []
    seen_names = set()
    connection = create_connection()

    # Fetch existing model names from the database
    cursor = connection.cursor()
    cursor.execute("SELECT model_name FROM models WHERE category = %s", (category,))
    existing_models = {row['model_name'] for row in cursor.fetchall()}

    for item_name in os.listdir(base_folder):
        item_path = os.path.join(base_folder, item_name)
        if os.path.isdir(item_path):
            models = []
            for filename in os.listdir(item_path):
                name_without_extension = os.path.splitext(filename)[0]
                if filename.endswith(image_extensions):
                    if name_without_extension in seen_names:
                        continue
                    model_name = name_without_extension
                    if model_name not in existing_models:
                        image_path = os.path.join(item_path, filename)
                        image_url = upload_to_azure(image_path, filename, AZURE_EXPIRATION_HOURS)
                        models.append({"name": model_name, "image_path": image_url})
                        seen_names.add(name_without_extension)
                        insert_model_data(connection, item_name, model_name, image_url, category)
                        existing_models.add(model_name)  # Add to existing models to prevent future uploads

            if not models:
                model_name = item_name
                models.append(
                    {"name": model_name, "image_path": "https://via.placeholder.com/75x112.png?text=No+Image"})
                insert_model_data(connection, item_name, model_name,
                                  "https://via.placeholder.com/75x112.png?text=No+Image", category)
                existing_models.add(model_name)  # Add to existing models to prevent future uploads

            folders.append({"name": item_name, "models": models})
        else:
            name_without_extension = os.path.splitext(item_name)[0]
            if item_name.endswith(image_extensions):
                if name_without_extension in seen_names:
                    continue
                model_name = name_without_extension
                if model_name not in existing_models:
                    image_path = item_path
                    image_url = upload_to_azure(image_path, item_name, AZURE_EXPIRATION_HOURS)
                    files.append({"name": model_name, "image_path": image_url})
                    seen_names.add(name_without_extension)
                    insert_model_data(connection, '', model_name, image_url, category)
                    existing_models.add(model_name)  # Add to existing models to prevent future uploads

    connection.close()
    return {"folders": folders, "files": files}