# -*- coding: future_fstrings -*-

from serial import Serial
from time import sleep
from struct import pack


SERIAL_BAUD = 115200

class PapaGuyItself:

    def __init__(self):
        self.log = []
        self.port = None
        self.connection = None


    def connect(self, port):
        self.port = port
        self.connection = Serial(port, baudrate=SERIAL_BAUD, timeout=.1)


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


papaguy = PapaGuyItself()
