import pickle as json
import json
import socket
from struct import Struct, calcsize
from select import select
from time import sleep

__all__ = ("Server", "Client", "localhostname", "localhost", "LAN", "WAN")

_int = "H" # 0 <= number <= 65535 == 2 ** 16 -1
_size = calcsize(_int)
_struct = Struct("!" + _int)

del Struct, calcsize # clear namespace

hostname = socket.gethostname()
host = socket.gethostbyname(hostname)

HOST = "localhost" # local device
LAN = host # local area network
WAN = "" # wide area network 

class BaseSocket(): # isim önerilerine açığım

    def __init__(self):
        self.socket = socket.socket()

    def close(self):
        """Closes socket."""
        self.socket.close()


class SelectWrapper():

    def wait_until(self, method, interval = 0.05):
        while not method():
            sleep(interval)

    def isreadable(self):
        """Returns True if socket can read data."""
        return select((self.socket,), (), (), 0)[0]

    def iswritable(self):
        """Returns True if socket can write data."""
        return select((), (self.socket,), (), 0)[1]
    
    def iserror(self):
        """Returns True if socket will raise error."""
        return select((), (), (self.socket,), 0)[2]

    def select(self):
        s = (self.socket,)
        return select(s, s, s, 0)


class Server(BaseSocket, SelectWrapper):
    """Server class for accepting clients."""

    isacceptable = SelectWrapper.isreadable # alias

    def bind(self, address):
        """Bind server to address."""
        self.socket.bind(address)

    def listen(self, n):
        """Set the number of unaccepted connections that the system will allow before refusing new connections."""
        self.socket.listen(n)

    def accept(self, block = False):
        """Accept a client and return it."""
        if not block:
            self.wait_until(self.isacceptable)
        return AcceptedClient(*self.socket.accept())
        

class BaseClient(SelectWrapper):

    def _safe_send(self, msg):
        totalsent = 0
        while totalsent < len(msg):
            sent = self.socket.send(msg[totalsent:])
            if sent:
                totalsent += sent
            else:
                raise ConnectionError("Socket connection is broken.")

    def _safe_recv(self, lenght, block = False):
        return_value = b""
        bytes_recd = 0
        while bytes_recd < lenght:
            if not block:
                self.wait_until(self.isreadable)
            chunk = self.socket.recv(lenght - bytes_recd)
            if chunk:
                return_value += chunk
                bytes_recd += len(chunk)
            else:
                raise ConnectionError("Socket connection is broken.")
        return return_value

    def send_obj(self, obj):
        """Send an object to the other socket."""
        bytes_to_send = json.dumps(obj).encode()
        self._safe_send(_struct.pack(len(bytes_to_send)) + bytes_to_send)

    def recv_obj(self, block = False):
        """Receive an object from the other socket."""
        lenght = _struct.unpack(self._safe_recv(_size))[0]
        return json.loads(self._safe_recv(lenght, block).decode())
        

class AcceptedClient(BaseClient, BaseSocket):

    def __init__(self, socket, addr):
        self.addr = addr
        self.socket = socket


class Client(BaseClient, BaseSocket):
    """Client class for connecting to the server."""

    def connect(self, address):
        """Connect to the server."""
        self.socket.connect(address)

class BroadcastListener:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('', 64321))
        self.ips = {}

    def update(self):
        while select((self.socket, ), (), (), 0)[0]:
            m = self.socket.recvfrom(1024)
            ip = m[1][0]
            flag, msg = m[0][0], m[0][1:]
            if flag:
                self.ips[ip] = msg
            else:
                try:
                    self.ips.remove(ip)
                except ValueError:
                    pass
        return self.ips
    
class Broadcaster:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def broadcast(self, bool_: bool, msg: bytes):
        """Cihazın bağlanmaya müsait olup olmadığını duyur."""
        if bool_:
            self.socket.sendto(b'\x01' + msg, ('255.255.255.255', 64321))
        else:
            self.socket.sendto(b'\x00' + msg, ('255.255.255.255', 64321))