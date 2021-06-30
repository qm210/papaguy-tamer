from serial import Serial
from time import sleep
from struct import pack
import serial.tools.list_ports


SERIAL_BAUD = 115200

LOG_LENGTH = 100

class PapaGuyItself:

    log = []
    port = None
    connection = None

    def __init__(self):
        self.clear_state()
        print("PapaGuyItself constructed.")

    def clear_state(self):
        self.port = None
        self.connection = None


    def connect(self, port):
        self.port = port
        self.connection = Serial(port, baudrate=SERIAL_BAUD, timeout=.1)
        while True:
            alive_signal = self.read_string()
            print("Waiting for response...")
            if len(alive_signal) > 0:
                break
            sleep(0.2)
        self.log = [alive_signal]
        print("PapaGuy appears to be alive.")


    def read_string(self) -> str:
        if self.connection is None:
            return ""
        return self.connection.readline().decode('utf-8').strip()


    def disconnect(self) -> str:
        if self.connection is None:
            return "Couldn't disconnect, cause nothing is connected :|"
        self.connection.close()
        self.clear_state()
        return "Disconnected."


    def serial_log(self):
        while self.connection is not None:
            sleep(1)
            data = self.read_string()
            if len(data) == 0:
                continue
            if len(self.log) == LOG_LENGTH:
                self.log.pop(0)
            self.log.append(str(data))
            print("DATA:", self.log)
        print("serial_log stopped, because connection happened to be None")


    def serial_send(self, target, value):
        message = bytearray(pack("B", target), pack(">H", value))
        print("SEND MESSAGE", message)
        if self.connection is None:
            print(f"Öhm. Cannot send when connection is not initialized. Do pls.")
            return
        self.connection.write(message)


    # could be @staticmethod, I guess
    def get_portlist(self):
        return [port.device for port in serial.tools.list_ports.comports()]


papaguy = PapaGuyItself()
