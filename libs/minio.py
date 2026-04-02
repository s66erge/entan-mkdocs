# ~/~ begin <<docs/gong-web-app/minio_access.md#libs/minio.py>>[init]

import os
import json
from io import BytesIO
import libs.utils as utils
import pandas as pd 
from minio import Minio
from minio.error import S3Error, MinioException

minio_client = None # global S3 client, initialized from main.py and used in transit

# on: F:\Other-apps\minio
# .\minio.exe server . --license .\minio.license
# console:  http://127.0.0.1:9001

# https://docs.min.io/enterprise/aistor-object-store/developers/sdk/python/


# ~/~ begin <<docs/gong-web-app/minio_access.md#define-client>>[init]

def create_minio_client():
    if utils.isa_dev_computer():
        client = Minio(
            endpoint ="localhost:9000",
            access_key = "dhamma-gong-on-local",
            secret_key = os.environ["MINIO_USER1_SECRET"],
            secure = False,
        )
    else: # production
        client = Minio(
            endpoint ="bucket.railway.internal:9000",
            access_key = "dhamma-gong-on-local-serge",
            secret_key = os.environ["MINIO_USER1_SECRET"],
            secure = False,
        )
    return client

# ~/~ end
# ~/~ begin <<docs/gong-web-app/minio_access.md#get-objects-alist>>[init]

def get_objects_list(bucket, prefix, recursive=False):
    listob = []
    for obj in minio_client.list_objects(bucket, prefix=prefix, recursive=recursive):
        listob.append(obj.object_name)
    return listob

# ~/~ end
# ~/~ begin <<docs/gong-web-app/minio_access.md#file-upload>>[init]

def file_upload(bucket, the_object, file_to_upload):
    result = minio_client.fput_object(
        bucket_name=bucket,
        object_name=the_object,
        file_path=file_to_upload,
    )
    return result
# ~/~ end
# ~/~ begin <<docs/gong-web-app/minio_access.md#file-download>>[init]
def file_download(bucket, the_object, file_to_write):
    result = minio_client.fget_object(
        bucket_name=bucket,
        object_name=the_object,
        file_path=file_to_write,
    )
    return result

# ~/~ end
# ~/~ begin <<docs/gong-web-app/minio_access.md#get-save-temp-files>>[init]

def get_center_temp_data(center, key):
    r2 = minio_client.get_object(utils.Globals.CENTER_BUCKET, f"{center}/temp/{key}")  
    raw = r2.read()                    # b'{"date": "2026-03-30"}'
    text = raw.decode("utf-8")         # '{"date": "2026-03-30"}'
    return json.loads(text)            # {'date': '2026-03-30'}

def save_center_temp_data(center, key, data):
    data_json = json.dumps(data)
    raw = data_json.encode("utf-8")     # b'{"date": "2026-03-30"}'
    length = len(raw)
    stream = BytesIO(raw)
    minio_client.put_object(utils.Globals.CENTER_BUCKET, f"{center}/temp/{key}", stream, length)  
    return

def remove_center_temp_data(center):
    list_obj = get_objects_list(utils.Globals.CENTER_BUCKET, f"{center}/temp/")
    for the_object in list_obj:
        minio_client.remove_object(utils.Globals.CENTER_BUCKET, the_object)
    return

# ~/~ end
# ~/~ begin <<docs/gong-web-app/minio_access.md#get-save-excel-files>>[init]

def save_excel_minio(center):
    if center == "all_centers":
        file_path = f"{utils.get_db_path()}all_centers.xlsx"
        the_object = "all_centers.xlsx"
    else:
        file_path = f"{utils.get_db_path()}{center}.xlsx"
        the_object = f"{center}/{center}.xlsx"
    file_upload(utils.Globals.CENTER_BUCKET, the_object, file_path)

def get_excel_minio(center):
    if center == "all_centers":
        file_path = f"{utils.get_db_path()}all_centers.xlsx"
        the_object = "all_centers.xlsx"
    else:
        file_path = f"{utils.get_db_path()}{center}.xlsx"
        the_object = f"{center}/{center}.xlsx"
    file_download(utils.Globals.CENTER_BUCKET, the_object, file_path)
    return file_path

def dicts_from_excel_minio(center, sheet):
    file_path = get_excel_minio(center)
    df = pd.read_excel(file_path, sheet_name=sheet)
    result = df.to_dict('records')
    return result

def params_from_excel_minio(center):
    list_of_dicts = dicts_from_excel_minio(center, "params")
    one_dict = {item["name"]: item["value"] for item in list_of_dicts}
    return one_dict


# ~/~ end

# ~/~ end
