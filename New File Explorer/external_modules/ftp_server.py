import sys
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

def start_ftp_server(directory, username, password, permissions="elradfmw"):
    authorizer = DummyAuthorizer()
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
    authorizer.add_user(username, password, directory, perm=permissions)
    handler = FTPHandler
    handler.authorizer = authorizer
    handler.banner = "Welcome to my FTP server."

    address = ("0.0.0.0", 21)
    server = FTPServer(address, handler)

    server.serve_forever()

if __name__ == "__main__":
    start_ftp_server(*[ arg for arg in sys.argv[1:]])
