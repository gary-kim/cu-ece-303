package main

import (
        "log"
        "net/http"

        "github.com/shurcooL/vfsgen"
)

func main() {
        var fs http.FileSystem = http.Dir("bindata/files")
        err := vfsgen.Generate(fs, vfsgen.Options{})
        if err != nil {
                log.Fatalln(err)
        }
}

