# Written by S. Mevawala, modified by D. Gitzel

import logging

import channelsimulator
import utils
import sys
import socket
import hashlib
import struct


class Receiver(object):

    def __init__(self, inbound_port=50005, outbound_port=50006, timeout=10, debug_level=logging.INFO):
        self.logger = utils.Logger(self.__class__.__name__, debug_level)

        self.inbound_port = inbound_port
        self.outbound_port = outbound_port
        self.simulator = channelsimulator.ChannelSimulator(inbound_port=inbound_port, outbound_port=outbound_port,
                                                           debug_level=debug_level)
        self.simulator.rcvr_setup(timeout)
        self.simulator.sndr_setup(timeout)

    def receive(self):
        raise NotImplementedError("The base API class has no implementation. Please override and add your own.")


class MyReceiver(Receiver):
    data = []

    def receive(self):
        while True:
            try:
                recv = self.simulator.u_receive()  # receive data
                data = self.decode(recv)
                if data[0] == -1:
                    continue
                tmp = []
                ack_bytes = struct.pack("I", data[0])
                for i in range(5):
                    tmp.extend(ack_bytes)
                self.simulator.u_send(bytearray(tmp))  # send ACK
                self.logger.info("Got frame and sent ACK for ACK #{}".format(data[0]))
                while len(self.data) <= data[0]:
                    self.data.append([])
                self.data[data[0]] = str(bytearray(data[1]))

            except socket.timeout:
                for d in self.data:
                    sys.stdout.write(d)
                sys.exit()

    def decode(self, frame):
        """
        Expects the raw frame data

        :returns: Returns a tuple of (ACK_NUM, DATA). Will be (-1, 0) if not recoverable
        """
        if len(frame) < 19:
            self.logger.info("Got frame that is below the minimum size of a frame. Ignoring")
            return -1, 0
        data = frame[0:-20]
        checked_data = frame[0:-16]
        ack_num = frame[-20:-16]
        checksum = frame[-16:]

        if not (bytes(bytearray(checksum)) == hashlib.md5(bytes(bytearray(checked_data))).digest()[:16]):
            self.logger.info("Received corrupted frame. Ignoring")
            return -1, 0

        return struct.unpack("I", bytes(bytearray(ack_num)))[0], data


class BogoReceiver(Receiver):
    ACK_DATA = bytes(123)

    def __init__(self):
        super(BogoReceiver, self).__init__()

    def receive(self):
        self.logger.info(
            "Receiving on port: {} and replying with ACK on port: {}".format(self.inbound_port, self.outbound_port))
        while True:
            try:
                data = self.simulator.u_receive()  # receive data
                self.logger.info("Got data from socket: {}".format(
                    data.decode('ascii')))  # note that ASCII will only decode bytes in the range 0-127
                sys.stdout.write(data)
                self.simulator.u_send(BogoReceiver.ACK_DATA)  # send ACK
            except socket.timeout:
                sys.exit()


if __name__ == "__main__":
    rcvr = MyReceiver()
    rcvr.receive()
