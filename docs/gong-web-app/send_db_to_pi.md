# Send database to center rasperry Pi

```{.python file=libs/send2pi.py}
import paramiko 
from scp import SCPClient   # scp module of paramiko
from pathlib import Path
import os
from datetime import datetime
from zoneinfo import ZoneInfo

# ssh -J pi@itadic.run.place:22 pi@localhost -p 7012

ports = {
    "Pajjota": 7011,
    "Mahi": 7012
}

<<session_connect>>
<<file_upload>>
<<file_download>>
<<main_program>>

```
### Upload a file

Transfer the database file (localDBfilePath) the remote control center using SCP (Secure Copy Protocol)
- destination path on the remote control center is given by remoteDBpath (e.g. "/home/pi/test" for both Pajjota and Mahi)
- should be used after a successful connection to the remote control center (RPI) through the jumpbox (RPI TUNNEL)

```{.python #file_upload}
def file_upload(localDBfilePath: Path, remoteDBpath: Path, session: paramiko.SSHClient):
    scp = SCPClient(session.get_transport())  # type: ignore
    # We will use Path().as_posix() to deal with the linux filesystem on the RPI !
    scp.put(str(localDBfilePath), str(remoteDBpath.as_posix()))
    # close the SCP connection
    scp.close()
```
### Download a file



```{.python #file_download}
def file_download(remoteDBfilePath: Path, localDBpath: Path, session: paramiko.SSHClient):
    scp = SCPClient(session.get_transport())  # type: ignore
    # We will use Path().as_posix() to deal with the linux filesystem on the RPI !
    scp.get(str(remoteDBfilePath.as_posix()), str(localDBpath))
    # close the SCP connection
    scp.close()

```
### Example of usage

Attention aux littéraux avec des backslashes :
- localDBfilepath = Path(r"C:\Users\Serge\Desktop\mahi.db")
ou alors
- localDBfilepath = Path("C:/Users/Serge/Desktop/mahi.db")
 

```{.python #main_program}
if __name__ == "__main__":
    localDBpath = Path("F:/myWinFolders/MyStuff/Downloads")
    localDBfilePath = localDBpath / "test.tmp"
    remoteDBpath = Path("/home/pi/test")
    remoteDBfilePath = remoteDBpath / "test22.tmp"
    session = session_connect(ports["Mahi"])
    # only is session is not None, we can try to upload the database file to
    # the remote control center (RPI)
    if session is not None:
        file_upload(localDBfilePath, remoteDBpath, session)
        file_download(remoteDBfilePath, localDBpath, session)

```

### Connect to ssh session via 'jumpbox'

Connect to the target RPI through the jumpbox (RPI TUNNEL) using paramiko.
We will use the jumpbox as a proxy to connect to the target RPI.

param rthjPort: the port on which the RPI is listening for
    ssh connections through the reverse tunnel (7011 for Pajjota, 7012 for Mahi)

Returns the SSH session if the connection is successful, None otherwise.

```{.python #session_connect}

def session_connect(rthjPort: int) -> paramiko.SSHClient | None:
    jumpbox_public_addr = "itadic.run.place"
    jumpbox_private_addr = '192.168.188.198'
    target_addr = 'localhost'
    targetPort = rthjPort  # rthj port   (e.g. : 7011)
    password = None   # using ssh key
    jumpbox = paramiko.SSHClient()
    jumpbox.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        # None : no password because using ssh key
        jumpbox.connect(jumpbox_public_addr, username='pi', password=password)
    except Exception as e:
        print(f"Connection to jumpbox (RPI TUNNEL) failed : {e}")
        return None
    else:
        jumpbox_transport = jumpbox.get_transport()
        src_addr = (jumpbox_private_addr, 22)
        dest_addr = (target_addr, targetPort)
        jumpbox_channel = jumpbox_transport.open_channel(  # type: ignore
            "direct-tcpip", dest_addr, src_addr)
        # we need to create a new session because we will connect
        #  to the target RPI through the jumpbox channel
        session = paramiko.SSHClient()
        # even for password authentication
        session.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        session.connect(target_addr, username='pi',
                            password=password, sock=jumpbox_channel)
        return session
```
