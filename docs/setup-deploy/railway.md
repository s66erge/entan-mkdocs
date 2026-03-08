# Railway

Railway is a platform that allows you to deploy applications easily. It provides a simple way to host your applications and manage their deployments.

Railway is connected to Github : all changes pushed to Github repo branch 'master' are deployed immediately (+/-) to Railway 'entan-mkdocs', where the 'main.py' file is the entry point.

## Using a dockerfile to drive the build 



## Railway CLI

### Installation

``` pwsh
scoop install railway
```

### Using it

The Railway CLI is used to:

1. link the local project to a Railway project:
   ``` pwsh
   railway login
   railway link
   ```
2. run the app localy with the Railway project environment variables:
   ``` pwsh
   railway run python main.py
   ```

## Resend api key

On the entan-mkdocs service in Railway, [define the variable 'RESEND_API_KEY'](../gong-web-app/utilities.md#via-resendcom)

## How to access a railway volume by installing a file browser ?

You can use a pre-made Filebrowser template service on Railway to inspect and download files from an existing volume. Below is a stepbystep workflow tailored to a single volume you already use in a project.

### Concept
Railway volumes are mounted into a service at a mount path (for example /app/storage), and appear there as a normal directory. The Volume File Browser template is a small helper service that mounts that same volume at /data and exposes a web UI where you can browse and download files.

### Preparation
1. Open the Railway project that contains the service currently using the volume you want to inspect.

2. Rightclick the volume, choose View settings, and note its current mount path (for example /permanent), because you need this later to restore it.

### Add the Volume File Browser service
1. In the same project, click the + New button and search for Volume File Browser, then add it as a new service.

2. In your original service that currently has the volume attached, remove the active deployment (threedot menu  Remove) so it will not keep trying to access the volume.

### Temporarily move the volume to the browser
1. Rightclick the volume and choose Disconnect to detach it from the original service.

2. Click the nowdisconnected volume, then click Mount and select the Volume File Browser service as the destination.

3. Use /permanent as the mount path for the file browser service and wait for that service to redeploy.

### Log in and browse files
1. Open the Variables tab for the Volume File Browser service and note the automatically generated basicauth username and password.

2. Click the Railwayprovided domain of the Volume File Browser service, log in with those credentials, and you will see the files from the volume under /permanent.

3. Upload/Download any files you need directly through this interface.

### Restore the volume to your app
1. Disconnect the volume from the Volume File Browser service once done.

2. Remount the volume back to the original service, using the original mount path you wrote down earlier (for example /permanent).

3. Redeploy the original service so it starts again with the volume attached.
