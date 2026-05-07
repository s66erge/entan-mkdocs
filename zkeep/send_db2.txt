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


def session_connect(rthjPort: int) -> paramiko.SSHClient | None:
    '''
    Connect to the target RPI through the jumpbox (RPI TUNNEL) using paramiko.
    We will use the jumpbox as a proxy to connect to the target RPI.

    param rthjPort: the port on which the RPI is listening for
        ssh connections through the reverse tunnel (7011 for Pajjota, 7012 for Mahi)

    Returns the SSH session if the connection is successful, None otherwise.
    '''
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
        try:
            session.connect(target_addr, username='pi',
                            password=password, sock=jumpbox_channel)
        except Exception as e:
            print(f"Connection to RPI failed : {e}")
            return None
        else:
            return session


def db_upload(localDBfilePath: Path, remoteDBpath: Path, session: paramiko.SSHClient):
    '''
    Transfer the database file (localDBfilePath) the remote control center using SCP
      (Secure Copy Protocol)
    - destination path on the remote control center is given by remoteDBpath
     (e.g. "/home/pi/test" for both Pajjota and Mahi)
    - should be used after a successful connection to the remote control center (RPI) through
    the jumpbox (RPI TUNNEL)
    '''
    scp = SCPClient(
        session.get_transport())  # type: ignore
    # try to copy to remote control center
    try:
        # We will use Path().as_posix() to deal with the linux filesystem on the RPI !
        scp.put(str(localDBfilePath), str(remoteDBpath.as_posix()))
    except Exception as e:
        print(f"Transfer failed : {e}")
    else:
        print("Transfer succeeded !")
    # close the SCP connection
    scp.close()

def db_download(remoteDBfilePath: Path, localDBpath: Path, session: paramiko.SSHClient):
    '''
    Transfer the database file (localDBfilePath) the remote control center using SCP
      (Secure Copy Protocol)
    - destination path on the remote control center is given by remoteDBpath
     (e.g. "/home/pi/test" for both Pajjota and Mahi)
    - should be used after a successful connection to the remote control center (RPI) through
    the jumpbox (RPI TUNNEL)
    '''
    scp = SCPClient(
        session.get_transport())  # type: ignore
    # try to copy to remote control center
    try:
        # We will use Path().as_posix() to deal with the linux filesystem on the RPI !
        scp.get(str(remoteDBfilePath.as_posix()), str(localDBpath), preserve_times=True)
    except Exception as e:
        print(f"Transfer failed : {e}")
    else:
        print("Transfer succeeded !")
    # close the SCP connection
    scp.close()

def to_utc_iso(dt_string: str, timezone: str = "Europe/Brussels") -> str:
    """
    Convert naive datetime string in given timezone to UTC ISO format.
    
    Args:
        dt_string: Naive datetime like '2026-03-10T09:53:22'
        timezone: IANA timezone like 'Europe/Brussels'
    
    Returns:
        UTC ISO string like '2026-03-10T08:53:22+00:00'
    """
    # Parse naive datetime (no timezone info)
    dt = datetime.fromisoformat(dt_string)
    
    # Make it timezone-aware (assume it's in the given timezone)
    tz = ZoneInfo(timezone)
    dt_local = dt.replace(tzinfo=tz)
    
    # Convert to UTC
    dt_utc = dt_local.astimezone(ZoneInfo("UTC"))
    
    # Return ISO format
    return dt_utc.isoformat()

if __name__ == "__main__":
    # Example of usage
    # Attention aux littéraux avec des backslashes :
    # localDBfilepath = Path(r"C:\Users\Serge\Desktop\mahi.db")
    # ou alors
    # localDBfilepath = Path("C:/Users/Serge/Desktop/mahi.db")
    localDBpath = Path("F:/myWinFolders/MyStuff/Downloads")
    localDBfilePath = localDBpath / "test.tmp"
    remoteDBpath = Path("/home/pi/test")
    remoteDBfilePath = remoteDBpath / "test22.tmp"
    session = session_connect(ports["Mahi"])
    # only is session is not None, we can try to upload the database file to
    # the remote control center (RPI)
    if session is not None:
        db_upload(localDBfilePath, remoteDBpath, session)
        db_download(remoteDBfilePath, localDBpath, session)
        full_path = localDBpath / "test22.tmp"
        mtime = os.path.getmtime(full_path)
        localtime = datetime.fromtimestamp(mtime).isoformat()
        utctime = to_utc_iso(localtime, 'Europe/Paris')
        print(f'local {localtime}, utc {utctime}')
