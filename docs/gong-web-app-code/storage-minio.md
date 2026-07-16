# Storage 'S3' : Minio


```python
#| file: libs/minio.py 

import os
from pathlib import Path
import libs.utils as utils
import pandas as pd 
from minio import Minio

minio_client = None # global S3 client, initialized from main.py and used in transit

# on: F:\Other-apps\minio
# .\minio.exe server . --address ":9005" --console-address ":9006" --license .\minio.license
# console:  http://127.0.0.1:9005

# https://docs.min.io/enterprise/aistor-object-store/developers/sdk/python/


<<define-client>>
<<get-objects-alist>>
<<file-upload>>
<<file-download>>
<<get-save-temp-files>>
<<get-save-excel-files>>

```

### Define the Minio client

```python
#| id: define-client

def create_minio_client():
    # 12-factor: all connection config comes from the environment, with
    # dev-friendly defaults so a bare `localhost` MinIO works out of the box.
    # Staging/production set MINIO_ENDPOINT (e.g. "minio:9000") and, on a
    # TLS-terminated setup, MINIO_SECURE=true.
    endpoint = os.environ.get("MINIO_ENDPOINT", "localhost:9000")
    access_key = os.environ.get("MINIO_ACCESS_KEY") or os.environ["MINIO_ROOT_USER"]
    secret_key = os.environ.get("MINIO_SECRET_KEY") or os.environ["MINIO_ROOT_PASSWORD"]
    secure = os.environ.get("MINIO_SECURE", "false").lower() == "true"
    return Minio(
        endpoint=endpoint,
        access_key=access_key,
        secret_key=secret_key,
        secure=secure,
        region="auto",
    )

```

### Get list of ojects in a bucket on a prefix

```python
#| id: get-objects-alist

def get_objects_list(bucket, prefix, recursive=True):
    listob = []
    for obj in minio_client.list_objects(bucket, prefix=prefix, recursive=recursive):
        listob.append(obj.object_name)
    return listob

def delete_object(bucket, prefix, object_name):
    result = minio_client.remove_object(
        bucket_name = bucket,
        object_name = f"{prefix}/{object_name}"
    )
    return result

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

def get_center_temp_df(center, df_name):
    file_path = f"{utils.get_db_path()}{center}{df_name}.parquet"
    df = pd.read_parquet(file_path)
    return df

def save_df_center_temp(center, df_name, df):
    file_path = f"{utils.get_db_path()}{center}{df_name}.parquet"
    df.to_parquet(file_path)
    return

def get_center_temp_list_of_dicts(center, key):
    df = get_center_temp_df(center, key)
    return df.to_dict(orient='records')

def save_center_temp_list_of_dicts(center, key, data):
    df = pd.DataFrame(data)
    save_df_center_temp(center, key, df)
    return

def remove_temp_center_data(center):
    folder = Path(utils.get_db_path())
    target_files = [
        file_path for file_path in folder.iterdir()
        if file_path.is_file() and file_path.name.startswith(center) and file_path.suffix == '.parquet'
    ]
    for file_path in target_files:
        file_path.unlink()
    return

```

### Get/save excel params files

```python
#| id: get-save-excel-files

def get_excel(center):
    if center == "all_centers":
        file_path = f"{utils.get_db_path()}all_centers.xlsx"
    else:
        file_path = f"{utils.get_db_path()}{center}.xlsx"
    return file_path

def remove_excel(center):
    config_path = f'{utils.get_db_path()}{center}.xlsx'
    if os.path.exists(config_path):
        os.remove(config_path)
    return

def dicts_from_excel(center, sheet):
    file_path = get_excel(center)
    df = pd.read_excel(file_path, sheet_name=sheet)
    result = df.to_dict('records')
    return result

def params_from_excel(center):
    list_of_dicts = dicts_from_excel(center, "params")
    one_dict = {item["name"]: item["value"] for item in list_of_dicts}
    return one_dict


```
