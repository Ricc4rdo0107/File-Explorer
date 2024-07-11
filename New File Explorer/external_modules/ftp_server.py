import sys
import logging
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def start_ftp_server(host: str, port: int, directory: str, username: str, password: str, permissions: str="elradfmw"):
    """
    params:
        permissions:
        "e": Change directory (CWD, CDUP commands)
        "l": List files (LIST, NLST, STAT, MLSD, MLST commands)
        "r": Retrieve file from the server (RETR command)
        "a": Append data to an existing file (APPE command)
        "d": Delete file or directory (DELE, RMD commands)
        "f": Rename file or directory (RNFR, RNTO commands)
        "m": Create directory (MKD command)
        "w": Store a file to the server (STOR, STOU commands)
        "M": Change file mode/permission (SITE CHMOD command)
        "T": Change file modification time (MFMT command)
    """
    try:
        logging.info(f"FTP_SERVER STARTED:\nAddress: {host}:{port}\nDirectory:{directory}"\
                     f"Username: {username}\nPassword: {'*' * len(password)}\nPermissions:{permissions}")
        authorizer = DummyAuthorizer()
        authorizer.add_user(username, password, directory, perm=permissions)
        handler = FTPHandler
        handler.authorizer = authorizer
        handler.banner = "Welcome to my FTP server."
        address = (host, port)
        server = FTPServer(address, handler)
        server.serve_forever()
    except Exception as e:
        with open("ftp_server_error_log.txt", "w") as error_log:
            error_log.write(str(e.with_traceback(None)))

if __name__ == "__main__":
    start_ftp_server(*[ arg for arg in sys.argv[1:]])
