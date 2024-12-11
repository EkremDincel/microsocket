import socket

try:
	from . import microsocket
except ImportError:
	import microsocket

import asyncio

SERIALIZER = microsocket.SERIALIZER
DESERIALIZER = microsocket.DESERIALIZER
_struct = microsocket._struct
_size = microsocket._size

YIELD_TO_LOOP = lambda: asyncio.sleep(0)

__all__ = ["AsyncServer", "AsyncClient", "YIELD_TO_LOOP"]


class AsyncBaseSocket(microsocket.BaseSocket):
	def __init__(self):
		self.socket = socket.socket()
		# self.socket.setblocking(False)


class AsyncSelectWrapper(microsocket.SelectWrapper):
	async def wait_until(self, method):
		while not method():
			await YIELD_TO_LOOP()


class AsyncServer(AsyncBaseSocket, AsyncSelectWrapper, microsocket.Server):
	async def accept(self):
		"""Accept a client and return it."""
		await self.wait_until(self.isreadable)
		return AsyncAcceptedClient(*self.socket.accept())


class AsyncBaseClient(AsyncBaseSocket, AsyncSelectWrapper, microsocket.BaseClient):
	async def _safe_send(self, msg):
		totalsent = 0
		while totalsent < len(msg):
			sent = self.socket.send(msg[totalsent:])
			if sent:
				totalsent += sent
			else:
				raise ConnectionError("Socket connection is broken.")
			await YIELD_TO_LOOP()

	async def _safe_recv(self, lenght):
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

	async def recv_obj(self):
		"""Receive an object from the other socket."""
		lenght = _struct.unpack(await self._safe_recv(_size))[0]
		return DESERIALIZER((await self._safe_recv(lenght)).decode())


class AsyncAcceptedClient(microsocket.AcceptedClient, AsyncBaseClient):
	pass


class AsyncClient(AsyncBaseClient, microsocket.Client):
	"""Client class for connecting to the server."""

	async def connect(self, address):
		"""Connect to the server."""
		while not self.iswritable():  # Note: BlockingIOError doesn't mean that the connection hasn't happened
			try:
				self.socket.connect(address)  # use settimeout instead?
			except BlockingIOError:
				pass
			await YIELD_TO_LOOP()


if __name__ == "__main__":

	async def display():
		anim = "|/-\\"
		x = 0
		while True:
			print(f"\r[{anim[x]}]", end="")
			x += 1
			x %= len(anim)
			await asyncio.sleep(0.25)

	async def main():
		asyncio.create_task(display())
		await AsyncClient().connect(("", 8000))

	asyncio.run(main())
