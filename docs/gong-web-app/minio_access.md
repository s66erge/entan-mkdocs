# Send database to center rasperry Pi

```python
#| file: libs/minio.py 

import os
from minio import Minio
from minio.error import S3Error, MinioException
import libs.utils as utils 

minio_client = None # global S3 client, initialized from main.py and used in transit

# on: F:\Other-apps\minio
# .\minio.exe server . --license .\minio.license
# console:  http://127.0.0.1:9001

<<define_client>>
<<get_objects_list>>
<<file_upload>>
<<file_download>>

```

### Define the Minio client

```python
#| id: define_client

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
#| id: get_objects_list

def minio_get_objects_list(client, bucket, prefix, recursive=False):
    listob = []
    for obj in client.list_objects(bucket, prefix=prefix, recursive=recursive):
        listob.append(obj.object_name)
    return listob

```
### Upload a file

```python
#| id: file_upload

def file_upload(client, bucket, the_object, file_to_upload):
    result = client.fput_object(
        bucket_name=bucket,
        object_name=the_object,
        file_path=file_to_upload,
    )
    return result
```

### Download a file

```python
#| id: file_download
def file_download(client, bucket, the_object, file_to_write):
    result = client.fget_object(
        bucket_name=bucket,
        object_name=the_object,
        file_path=file_to_write,
    )
    return result

```
