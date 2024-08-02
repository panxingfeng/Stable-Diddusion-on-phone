from azure.storage.blob import BlobServiceClient, BlobSasPermissions, generate_blob_sas
from datetime import datetime, timedelta, timezone

# Azure存储的连接信息
AZURE_CONNECTION_STRING = ""
AZURE_CONTAINER_NAME = ""
blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)

def upload_to_azure(local_path, blob_name, time):
    try:
        container_client = blob_service_client.get_container_client(AZURE_CONTAINER_NAME)
        blob_client = container_client.get_blob_client(blob_name)

        with open(local_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)

        sas_token = generate_blob_sas(
            account_name=blob_service_client.account_name,
            container_name=AZURE_CONTAINER_NAME,
            blob_name=blob_name,
            account_key=blob_service_client.credential.account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.now(timezone.utc) + timedelta(hours=time)
        )

        azure_blob_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{AZURE_CONTAINER_NAME}/{blob_name}?{sas_token}"
        return azure_blob_url
    except Exception as e:
        print(f"上传到Azure时遇到异常: {e}")
        return None