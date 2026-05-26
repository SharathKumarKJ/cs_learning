package main

import (
	"fmt"
	"io"
	"net/http"
	"sync"
)

func main() {
	sem := make(chan struct{}, 2)
	var wg sync.WaitGroup
	urls := []string{"https://www.google.com", "https://www.google.com", "https://www.google.com", "https://www.google.com", "https://www.google.com/"}

	for _, url := range urls {
		wg.Add(1)
		go func(u string) {
			defer wg.Done()
			sem <- struct{}{}
			defer func() { <-sem }()

			res, err := http.Get(u)
			if err != nil {
				fmt.Println(err)
				return
			}
			defer res.Body.Close()

			data, err := io.ReadAll(res.Body)
			if err != nil {
				fmt.Println(err)
				return
			}
			fmt.Println(len(data))
		}(url)
	}
	wg.Wait()
}
