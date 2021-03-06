# Written by S. Mevawala, modified by D. Gitzel

import logging
import socket

import channelsimulator
import utils
import sys
import threading
import hashlib
from collections import Counter
import time
import struct


class Sender(object):

    def __init__(self, inbound_port=50006, outbound_port=50005, timeout=10, debug_level=logging.INFO):
        self.logger = utils.Logger(self.__class__.__name__, debug_level)

        self.inbound_port = inbound_port
        self.outbound_port = outbound_port
        self.simulator = channelsimulator.ChannelSimulator(inbound_port=inbound_port, outbound_port=outbound_port,
                                                           debug_level=debug_level)
        self.simulator.sndr_setup(timeout)
        self.simulator.rcvr_setup(timeout)

    def send(self, data):
        raise NotImplementedError("The base API class has no implementation. Please override and add your own.")


class MySender(Sender):
    data = []
    acks = []
    jobs = []
    num_acks = 0
    num_jobs = 0

    def send(self, data):
        self.logger.info(
            "Sending on port: {} and waiting for ACK on port: {}".format(self.outbound_port, self.inbound_port))

        ack_start = len(self.data)
        d = self.split_data(0, data)
        num_frames = len(d)
        self.data.extend(d)
        self.acks.extend([False for i in range(num_frames)])
        self.num_jobs += num_frames
        now = time.time()
        self.jobs.extend([(i, now) for i in range(ack_start, ack_start + num_frames)])

        # Start sending thread.
        _send = threading.Thread(target=self._send)
        _send.daemon = True
        _send.start()

        # Main thread becomes ACK receiving thread
        self.recv_ack()

    def split_data(self, ack_start, data_bytes):
        """
        Splits the given data up into 1024 byte frames.

        The format of the frames will be as follows:
        * 1-1004 bytes of data
        * 4 bytes for ACK num
        * 16 bytes for checksum

        :param ack_start: the beginning ACK number
        :param data_bytes: the data to be sent
        :return: list of list of bytes to be sent as data to the receiver
        """
        SIZE = 1004

        # This section is stolen then modified from the `channelsimulator.py` file
        frames = list()
        num_bytes = len(data_bytes)
        extra = 1 if num_bytes % SIZE else 0

        for i in xrange(num_bytes / SIZE + extra):
            # split data into 1024 byte frames
            frames.append(
                self.make_frame(
                    ack_start + i,
                    data_bytes[
                        i * SIZE:
                        i * SIZE + SIZE
                    ]
                )

            )
        return frames

    def make_frame(self, ack_num, data):
        """
        This function creates a frame from a given ACK number and data.
        The data should be 1004 bytes or less.

        :param ack_num: the ACK number of this frame
        :param data: the data that should be in this frame
        :return: list of bytes making up a 1024 byte frame
        """
        d = []
        d.extend(data)
        d.extend(struct.pack("I", ack_num))
        d.extend(hashlib.md5(bytes(bytearray(d))).digest()[:16])
        return d

    def _send(self):
        """
        Function meant to be started on a separate thread
        to handle sending data frames to the receiver.
        """
        while True:
            try:
                if self.jobs:
                    if self.jobs[0][1] < time.time():
                        job = self.jobs.pop(0)
                        if self.acks[job[0]]:
                            continue
                        self.simulator.u_send(bytearray(self.data[job[0]]))
                        self.logger.info("Sending data with ACK #{}".format(job[0]))
                        self.jobs.append((job[0], time.time() + 0.005))
                    else:
                        time.sleep(max(self.jobs[0][1] - time.time(), 0))
                else:
                    sys.exit()
            except socket.timeout:
                pass

    def recv_ack(self):
        """
        Function for receiving ACKs from the receiver
        """
        while True:
            raw_ack = self.simulator.u_receive()
            if len(raw_ack) != 20:
                self.logger.info("Received ACK that is not 20 bytes")
                continue
            ack = [0, 0, 0, 0, 0]
            for i in range(0, 5):
                ack[i] = struct.unpack("I", bytes(bytearray(raw_ack[i * 4:(i * 4) + 4])))[0]
            data = Counter(ack).most_common()
            if data[0][1] < 3:  # The ACK seems quite corrupted. Let's just ignore it
                self.logger.info("Ignoring very corrupted ACK")
                continue

            if data[0][1] < 5:
                self.logger.info("Recovered ACK #{}".format(data[0][0]))

            self.logger.info("Recieved ACK: {}".format(int(data[0][0])))
            if not self.acks[int(data[0][0])]:
                self.acks[int(data[0][0])] = True
                self.num_acks = self.num_acks + 1

            if self.num_acks >= self.num_jobs and all(ack is True for ack in self.acks):
                sys.exit()


class BogoSender(Sender):

    def __init__(self):
        super(BogoSender, self).__init__()

    def send(self, data):
        self.logger.info(
            "Sending on port: {} and waiting for ACK on port: {}".format(self.outbound_port, self.inbound_port))
        while True:
            try:
                self.simulator.u_send(data)  # send data
                ack = self.simulator.u_receive()  # receive ACK
                self.logger.info("Got ACK from socket: {}".format(
                    ack.decode('ascii')))  # note that ASCII will only decode bytes in the range 0-127
                break
            except socket.timeout:
                pass


if __name__ == "__main__":
    # test out BogoSender
    DATA = bytearray(sys.stdin.read())
    sndr = MySender()
    sndr.send(DATA)
