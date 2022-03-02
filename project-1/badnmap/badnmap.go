//go:generate go run ./bindata/assets_generate.go
//
//    Copyright (C) 2022 Gary Kim <gary@garykim.dev>
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
package main

import (
	"fmt"
	"os"

	"gomod.garykim.dev/cu-ece-303/project-1/badnmap/cmd"
)

func main() {
	if err := cmd.Execute(assets); err != nil {
		_, _ = fmt.Fprintf(os.Stderr, "ERROR: %s\n", err)
	}
}
