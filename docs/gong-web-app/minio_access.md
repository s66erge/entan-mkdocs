# Get/send file/data to minio for center rasperry Pi and local files



```python
#| file: libs/minio.py 

import os
import json
from minio import Minio
from minio.error import S3Error, MinioException
import libs.utils as utils 

minio_client = None # global S3 client, initialized from main.py and used in transit

# on: F:\Other-apps\minio
# .\minio.exe server . --license .\minio.license
# console:  http://127.0.0.1:9001

# https://docs.min.io/enterprise/aistor-object-store/developers/sdk/python/


<<define-client>>
<<get-objects-alist>>
<<file-upload>>
<<file-download>>
<<get-save-temp-files>>

```

### Define the Minio client

```python
#| id: define-client

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

```

### Get list of ojects in a bucket on a prefix

```python
#| id: get-objects-alist

def minio_get_objects_list(bucket, prefix, recursive=False):
    listob = []
    for obj in minio_client.list_objects(bucket, prefix=prefix, recursive=recursive):
        listob.append(obj.object_name)
    return listob

```
### Upload a file

```python
#| id: file-upload

def file_upload(bucket, the_object, file_to_upload):
    result = minio_client.fput_object(
        bucket_name=bucket,
        object_name=the_object,
        file_path=file_to_upload,
    )
    return result
```

### Download a file

```python
#| id: file-download
def file_download(bucket, the_object, file_to_write):
    result = minio_client.fget_object(
        bucket_name=bucket,
        object_name=the_object,
        file_path=file_to_write,
    )
    return result

```

### Get/save temp files

```python
#| id: get-save-temp-files

def get_center_temp_data(center, key):
    r2 = minio_client.get_object(utils.Globals.CENTER_BUCKET, f"{center}/temp/{key}")  
    raw = r2.read()                    # b'{"date": "2026-03-30"}'
    text = raw.decode("utf-8")         # '{"date": "2026-03-30"}'
    return json.loads(text)            # {'date': '2026-03-30'}

def save_center_temp_data(center, key, data):
    data_json = json.dumps(data)
    raw = data_json.encode("utf-8")     # b'{"date": "2026-03-30"}'
    length = len(raw)
    minio_client.put_object(utils.Globals.CENTER_BUCKET, f"{center}/temp/{key}", raw, length)  
    return

```
