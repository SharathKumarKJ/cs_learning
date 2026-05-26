// Strategy: swap algorithm at runtime via interface.
package main

import "fmt"

type Compressor interface {
	Compress(data []byte) []byte
}

type gzipC struct{}

func (gzipC) Compress(d []byte) []byte { return append([]byte("gz:"), d...) }

type zstdC struct{}

func (zstdC) Compress(d []byte) []byte { return append([]byte("zstd:"), d...) }

func Save(data []byte, c Compressor) {
	fmt.Println(string(c.Compress(data)))
}

func main() {
	Save([]byte("hello"), gzipC{})
	Save([]byte("hello"), zstdC{})
}
