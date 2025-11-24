# Railway

Railway is a platform that allows you to deploy applications easily. It provides a simple way to host your applications and manage their deployments.

## New instruction for this repo

Railway connected to Github : all changes pushed to Github repo branch 'master' are deployed immediately (+/-) to Railway 'entan-mkdocs', where the 'main.py' file is the entry point.

### Railway CLI

#### Installation

``` pwsh
scoop install railway
```

#### Using it

The Railway CLI is used to:

1. link the local project to a Railway project:
   ``` pwsh
   railway link
   ```
2. run the app localy with the Railway project environment variables:
   ``` pwsh
   railway run python main.py
   ```

### Resend api key

On the entan-mkdocs service in Railway, [define the variable 'RESEND_API_KEY'](../gong-web-app/utilities.md#via-resendcom)

### How to access a railway volume by installing a file browser ?

You can use a pre-made “Filebrowser” template service on Railway to inspect and download files from an existing volume. Below is a step‑by‑step workflow tailored to a single volume you already use in a project.​

#### Concept
Railway volumes are mounted into a service at a mount path (for example /app/storage), and appear there as a normal directory. The “Volume File Browser” template is a small helper service that mounts that same volume at /data and exposes a web UI where you can browse and download files.​

#### Preparation
1. Open the Railway project that contains the service currently using the volume you want to inspect.​

2. Right‑click the volume, choose “View settings,” and note its current mount path (for example /permanent), because you need this later to restore it.​

#### Add the Volume File Browser service
1. In the same project, click the “+ New” button and search for “Volume File Browser”, then add it as a new service.​

2. In your original service that currently has the volume attached, remove the active deployment (three‑dot menu → “Remove”) so it will not keep trying to access the volume.​

#### Temporarily move the volume to the browser
1. Right‑click the volume and choose “Disconnect” to detach it from the original service.​

2. Click the now‑disconnected volume, then click “Mount” and select the “Volume File Browser” service as the destination.​

3. Use /permanent as the mount path for the file browser service and wait for that service to redeploy.​

#### Log in and browse files
1. Open the “Variables” tab for the Volume File Browser service and note the automatically generated basic‑auth username and password.​

2. Click the Railway‑provided domain of the Volume File Browser service, log in with those credentials, and you will see the files from the volume under /permanent.​

3. Upload/Download any files you need directly through this interface.​

#### Restore the volume to your app
1. Disconnect the volume from the Volume File Browser service once done.​

2. Re‑mount the volume back to the original service, using the original mount path you wrote down earlier (for example /permanent).​

3. Redeploy the original service so it starts again with the volume attached.​

## Previous instructions

### Setup
Run the commands below on your local machine.
```pwsh
git clone https://github.com/AnswerDotAI/fh-deploy.git
cd railway
pip install -r requirements.txt
```

### Run the app locally
```pwsh
python main.py
```
### Deploying to Railway
- create a Railway [account](https://railway.app/) and signup to the Hobby plan. 
- install the Railway [CLI](https://docs.railway.app/guides/cli#installing-the-cli).
- run `railway login` to log in to your Railway account.
- run `fh_railway_deploy YOUR_APP_NAME`.

 Your app's entry point must be located in a `main.py` file for this to work.

### Supplementary Info.

#### what's in `fh_railway_deploy`
`fh_railway_deploy` runs the following commands behind the scenes for you:

```bash
railway init -n <app-name>
railway up -c
railway domain
railway link ...
railway volume add -m /permanent
```

It handles automatically linking your current app to a railway project, setting up all the environment variables such as the port to listen on and setting up a `requirements.txt` if you haven't one already.


#### Changing the start command or sleep directive or ...

Put a `railway.toml` file in the top application folder :

```toml
[build]
builder = "NIXPACKS"

[deploy]
numReplicas = 1
sleepApplication = true
startCommand = "uvicorn main:app --host 0.0.0.0 --port $PORT"
```

#### Customizing your Domain Name

Railway automatically assigns your website a unique domain name such as `quickdraw-production.up.railway.app`. However, if you want to use your own that you've purchased through services like [GoDaddy](https://www.godaddy.com/) or [Squarespace Domains](https://domains.squarespace.com/) and have users be able to navigate to your site using that domain, you'll need to configure it both in your domain registration service and in Railway. Railway has put together a nice tutorial for setting it up [here](https://docs.railway.app/guides/public-networking#custom-domains).

Make sure to notice the difference between setting up a regular domain and a subdomain. Regular domains don't have any prefixes before the main site name such as `example.com` and is setup differently from a subdomain which might look like `subdomain.example.com`. Make sure to follow your domain registration service's documentation on how to set these types up.