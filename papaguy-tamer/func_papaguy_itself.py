from serial import Serial
from time import sleep
from struct import pack
import serial.tools.list_ports


SERIAL_BAUD = 115200

class PapaGuyItself:

    def __init__(self):
        self.log = []
        self.port = None
        self.connection = None
        print("PapaGuyItself constructed.")


    def connect(self, port):
        self.port = port
        self.connection = Serial(port, baudrate=SERIAL_BAUD, timeout=.1)
        while True:
            alive_signal = self.connection.readline()
            print("Waiting for response...", alive_signal)
            if len(alive_signal) > 0:
                break
        print("PapaGuy appears to be alive.")


    def serial_log(self):
        while True:
            sleep(1)
            data = self.connection.readline()
            self.log.append(data)
            print("DATA:", data)


    def serial_send(self, target, value):
        message = bytearray(pack("B", target), pack(">H", value))
        print("SEND MESSAGE", message)
        if self.connection is None:
            print(f"Öhm. Cannot send when connection is not initialized. Do pls.")
            return
        self.connection.write(message)


    # @staticmethod
    def get_portlist(self):
        return [port.device for port in serial.tools.list_ports.comports()]


papaguy = PapaGuyItself()
