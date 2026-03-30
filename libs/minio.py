# ~/~ begin <<docs/gong-web-app/minio_access.md#libs/minio.py>>[init]

import os
from minio import Minio
from minio.error import S3Error, MinioException
import libs.utils as utils 

minio_client = None # global S3 client, initialized from main.py and used in transit

# on: F:\Other-apps\minio
# .\minio.exe server . --license .\minio.license
# console:  http://127.0.0.1:9001

# ~/~ begin <<docs/gong-web-app/minio_access.md#define_client>>[init]

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
            endpoint ="bucket-production-6009.up.railway.app:443",
            access_key = "dhamma-gong-on-local-serge",
            secret_key = os.environ["MINIO_USER1_SECRET"],
            secure = True,
        )
    return client

# ~/~ end
# ~/~ begin <<docs/gong-web-app/minio_access.md#get_objects_list>>[init]

def minio_get_objects_list(client, bucket, prefix, recursive=False):
    listob = []
    for obj in client.list_objects(bucket, prefix=prefix, recursive=recursive):
        listob.append(obj.object_name)
    return listob

# ~/~ end
# ~/~ begin <<docs/gong-web-app/minio_access.md#file_upload>>[init]

def file_upload(client, bucket, the_object, file_to_upload):
    result = client.fput_object(
        bucket_name=bucket,
        object_name=the_object,
        file_path=file_to_upload,
    )
    return result
# ~/~ end
# ~/~ begin <<docs/gong-web-app/minio_access.md#file_download>>[init]
def file_download(client, bucket, the_object, file_to_write):
    result = client.fget_object(
        bucket_name=bucket,
        object_name=the_object,
        file_path=file_to_write,
    )
    return result

# ~/~ end

# ~/~ end
