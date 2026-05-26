// Worker pool: fixed number of workers consuming jobs from a channel.
// Pattern of choice for bounded concurrency over a stream of tasks.
package main

import (
	"fmt"
	"sync"
	"time"
)

type Job struct {
	ID  int
	Pay int
}

type Result struct {
	JobID  int
	Output int
}

func worker(id int, jobs <-chan Job, results chan<- Result, wg *sync.WaitGroup) {
	defer wg.Done()
	for job := range jobs {
		time.Sleep(50 * time.Millisecond) // simulate work
		results <- Result{JobID: job.ID, Output: job.Pay * 2}
		fmt.Printf("worker %d processed job %d\n", id, job.ID)
	}
}

func main() {
	const numWorkers = 3
	const numJobs = 10

	jobs := make(chan Job, numJobs)
	results := make(chan Result, numJobs)

	var wg sync.WaitGroup
	for w := 1; w <= numWorkers; w++ {
		wg.Add(1)
		go worker(w, jobs, results, &wg)
	}

	for j := 1; j <= numJobs; j++ {
		jobs <- Job{ID: j, Pay: j * 10}
	}
	close(jobs) // tell workers no more jobs are coming.

	go func() { wg.Wait(); close(results) }() // close results once workers are done.

	for r := range results {
		fmt.Printf("result job=%d out=%d\n", r.JobID, r.Output)
	}
}
