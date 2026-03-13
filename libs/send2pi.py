# ~/~ begin <<docs/gong-web-app/send_db_to_pi.md#libs/send2pi.py>>[init]
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

# ~/~ begin <<docs/gong-web-app/send_db_to_pi.md#session_connect>>[init]

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
# ~/~ end
# ~/~ begin <<docs/gong-web-app/send_db_to_pi.md#file_upload>>[init]
def file_upload(localDBfilePath: Path, remoteDBpath: Path, session: paramiko.SSHClient):
    scp = SCPClient(
        session.get_transport())  # type: ignore
    # We will use Path().as_posix() to deal with the linux filesystem on the RPI !
    scp.put(str(localDBfilePath), str(remoteDBpath.as_posix()))
    # close the SCP connection
    scp.close()
# ~/~ end
# ~/~ begin <<docs/gong-web-app/send_db_to_pi.md#file_download>>[init]
def file_download(remoteDBfilePath: Path, localDBpath: Path, session: paramiko.SSHClient):
    scp = SCPClient(
        session.get_transport())  # type: ignore
    # We will use Path().as_posix() to deal with the linux filesystem on the RPI !
    scp.get(str(remoteDBfilePath.as_posix()), str(localDBpath))
    # close the SCP connection
    scp.close()
# ~/~ end
# ~/~ begin <<docs/gong-web-app/send_db_to_pi.md#main_program>>[init]
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

# ~/~ end

# ~/~ end
