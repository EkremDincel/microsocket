import microsocket

import asyncio
YIELD_TO_LOOP = lambda: asyncio.sleep(0)

__all__ = ["AsyncServer", "AsyncClient", "YIELD_TO_LOOP"]

class AsyncSelectWrapper(microsocket.SelectWrapper):

    async def wait_until(self, method):
        while not method():
            await YIELD_TO_LOOP()


class AsyncServer(AsyncSelectWrapper, microsocket.Server):

    async def accept(self):
        """Accept a client and return it."""
        await self.wait_until(self.isreadable)
        return AcceptedClient(*self.socket.accept())


class AsyncBaseClient(AsyncSelectWrapper, microsocket.BaseClient):

    async def _safe_send(self, msg):
        totalsent = 0
        while totalsent < len(msg):
            sent = self.socket.send(msg[totalsent:])
            if sent:
                totalsent += sent
            else:
                raise ConnectionError("Socket connection is broken.")
            await YIELD_TO_LOOP()

    async def _safe_recv(self, lenght, block = False):
        return_value = b""
        bytes_recd = 0
        while bytes_recd < lenght:
            await self.wait_until(self.isreadable)
            chunk = self.socket.recv(lenght - bytes_recd)
            if chunk:
                return_value += chunk
                bytes_recd += len(chunk)
            else:
                raise ConnectionError("Socket connection is broken.")
        return return_value

    async def send_obj(self, obj):
        """Send an object to the other socket."""
        bytes_to_send = SERIALIZER(obj).encode()
        await self._safe_send(_struct.pack(len(bytes_to_send)) + bytes_to_send)

    async def recv_obj(self, block = False):
        """Receive an object from the other socket."""
        lenght = _struct.unpack(self._safe_recv(_size))[0]
        return DESERIALIZER(await self._safe_recv(lenght, block).decode())


class AsyncAcceptedClient(AsyncBaseClient, microsocket.AcceptedClient):
    pass


class AsyncClient(AsyncBaseClient, microsocket.Client):
    """Client class for connecting to the server."""

    async def connect(self, address): # TODO: how connect asynchronously?
        """Connect to the server."""
        self.socket.connect(address)