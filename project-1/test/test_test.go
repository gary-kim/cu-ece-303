package main

import (
    "net"
    "fmt"
)

/*
#include <linux/tcp.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <netinet/in.h>
#include <errno.h>
#include <stdio.h>

int getTTL(int fd) {
    int val;
    socklen_t size = sizeof(val);
    setsockopt(fd, IPPROTO_IP, IP_RECVTTL, &(int) {1}, sizeof(int));
    printf("ERROR: %i\n", errno);
    errno = 0;
    getsockopt(fd, IPPROTO_IP, IP_TTL, &val, &size);
    printf("ERROR: %i\n", errno);
    return val;
}

int getMSS(int fd) {
    struct tcp_info ti;
    socklen_t tisize = sizeof(ti);
    getsockopt(fd, IPPROTO_TCP, TCP_INFO, &ti, &tisize);
    return ti.tcpi_rcv_space;
}
*/
import "C"

func main() {
//    taddr, err := net.ResolveTCPAddr("tcp", "nextnano.ee.cooper.edu:3389")
    taddr, err := net.ResolveTCPAddr("tcp", "ice03.ee.cooper.edu:31415")
    conn, err := net.DialTCP("tcp", nil, taddr)
    if err != nil {
        fmt.Println("ERROR 1: ", err)
        return;
    }
    rawConn, err := conn.SyscallConn()
    if err != nil {
        fmt.Println("ERROR 2: ", err)
        return;
    }

    printInfo := func(fd uintptr) {
        value := C.getMSS((C.int) (int(fd)))
        value2 := C.getTTL((C.int) (int(fd)))
        fmt.Println("Got TTL of: ", value2, " with an MSS of ", value)
    }
    rawConn.Control(printInfo)
}
