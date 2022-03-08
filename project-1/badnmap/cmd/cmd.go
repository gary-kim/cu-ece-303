// Package cmd implements the commands of badnmap
//
//   Copyright (C) 2022 Gary Kim <gary@garykim.dev>
//
//    This program is free software: you can redistribute it and/or modify
//    it under the terms of the GNU Affero General Public License as published
//    by the Free Software Foundation, either version 3 of the License, or
//    (at your option) any later version.
//
//    This program is distributed in the hope that it will be useful,
//    but WITHOUT ANY WARRANTY; without even the implied warranty of
//    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//    GNU Affero General Public License for more details.
//
//    You should have received a copy of the GNU Affero General Public License
//    along with this program.  If not, see <https://www.gnu.org/licenses/>.
//
package cmd

import (
	"errors"
	"fmt"
	"io/ioutil"
	"net"
	"net/http"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/spf13/cobra"
)

var portRangeStr string
var timeout time.Duration
var portUse map[int]string = make(map[int]string)
var parallel int

// Root is badnmap's root command
var Root = &cobra.Command{
	Use:   "badnnmap (address)",
	Short: "badnmap is a bad version of nmap",
	Long:  `badnmap will attempt to connect to various ports via tcp`,
	Run: func(command *cobra.Command, args []string) {
		if len(args) < 1 {
			_ = command.Usage()
			return
		}
		addrStr := args[0]
		portRange := strings.Split(portRangeStr, ":")

		if len(portRange) > 2 {
			exit(errors.New("cannot interpret given port range"))
		}

		var ports []int
		if portRangeStr == "" {
			ports = makeRange(0, 65535)
		} else {
			range1, err := strconv.Atoi(portRange[0])
			if err != nil {
				exit(err)
			}
			range2 := range1
			if len(portRange) == 2 {
				range2, err = strconv.Atoi(portRange[1])
				if err != nil {
					exit(err)
				}
			}

			ports = makeRange(range1, range2)
		}

		d := net.Dialer{Timeout: timeout}
		sem := make(chan bool)

		go func() {
			for i := 0; i < parallel; i++ {
				sem <- true
			}
		}()

		for _, p := range ports {
			<-sem
			go testPort(addrStr, p, sem, &d)
		}

		for i := 0; i < parallel; i++ {
			<-sem
		}
	},
}

func init() {
	Root.PersistentFlags().StringVarP(&portRangeStr, "port", "p", "", "Indicates the ports to scan. Can be a range in the format 80:100 as well")
	Root.PersistentFlags().DurationVarP(&timeout, "timeout", "t", 2000*1000*1000, "Timeout for tcp connection")
	Root.PersistentFlags().IntVar(&parallel, "parallel", 10, "Number of parallel connections")
}

// testPort tests the given port on the given address
func testPort(addr string, port int, sem chan bool, d *net.Dialer) {
	defer func() { sem <- true }()
	conn, err := d.Dial("tcp", addr+":"+strconv.Itoa(port))
	if err != nil {
		return
	}
	_ = conn.Close()
	use, valid := portUse[port]
	if valid {
		fmt.Printf("OPEN: %d, likely to be %s\n", port, use)
	} else {
		fmt.Printf("OPEN: %d, use unknown\n", port)
	}
}

// Execute executes the program
func Execute(fs http.FileSystem) error {
	sv, err := fs.Open("services")
	if err != nil {
		return err
	}

	st, err := ioutil.ReadAll(sv)
	if err != nil {
		return err
	}

	s := string(st)

	services := strings.Split(s, "\n")

	for _, service := range services {
		if strings.HasPrefix(service, "#") {
			continue
		}
		sev := strings.Fields(strings.Split(service, "#")[0])
		if len(sev) < 2 {
			continue
		}
		if !strings.HasSuffix(sev[1], "tcp") {
			continue
		}

		portStr := strings.Split(sev[1], "/")[0]

		port, err := strconv.Atoi(portStr)
		if err != nil {
			return err
		}

		portUse[port] = sev[0]
	}

	if err := Root.Execute(); err != nil {
		return err
	}
	return nil
}

// order not actually important
func makeRange(min int, max int) (tr []int) {
	if min > max {
		tmp := min
		min = max
		max = tmp
	}

	tr = make([]int, max-min+1)
	for i := min; i <= max; i++ {
		tr[i-min] = i
	}
	return
}

func exit(err error) {
	_, _ = fmt.Fprintf(os.Stderr, "ERROR: %s", err)
	os.Exit(1)
}
