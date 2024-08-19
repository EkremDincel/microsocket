from microsocket import Server, Client, BroadcastListener, Broadcaster, LAN
from time import sleep

PORT = 3030

def main():
	name = input("Adınız:\n > ")
	
	client = [True, False][int(input("Başkasına bağlanmak için 1, bağlantı beklemek için 2'ye basın.\n > ")) - 1]
	
	if client:
		listener = BroadcastListener()

		devices = listener.update()
		while not devices:
			devices = listener.update()

		print("Bağlanacak birini seçin:")
		for n, (ip, tag) in enumerate(devices.items(), 1):
			print(f"{n}: {tag.decode()} ({ip})")
		number = input(" > ")

		ip = tuple(devices)[int(number) - 1]

		conn = Client()
		conn.connect((ip, PORT))
	else:

		print(f"Bağlanacak cihazlar bekleniyor (bu cihazın adresi: {LAN}).")
		conn = Server()

		conn.bind((LAN, PORT))
		conn.listen(1)

		caster = Broadcaster()
		while True:
			caster.broadcast(True, name.encode())
			if conn.isreadable():
				conn = conn.accept()
				break
			sleep(0.5)

	conn.send_obj(name)
	other_name = conn.recv_obj()
	print(f"{other_name} ile bağlantı kuruldu.")

	turn = client
	while True:
		if turn:
			msg_to_send = input(" > ")
			conn.send_obj(msg_to_send)
			print(f"\033[0C\033[1A\rSiz: {msg_to_send}")
		else:
			print(f"{other_name}: {conn.recv_obj()}")
		turn = not turn

if __name__ == "__main__":
	try:
		main()
	except KeyboardInterrupt:
		print("Shutting down.")