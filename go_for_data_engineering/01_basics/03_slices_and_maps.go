// Slices and maps — the workhorses of Go data manipulation.
package main

import "fmt"

func main() {
	// Slice: dynamic-length view over an array.
	nums := []int{1, 2, 3}
	nums = append(nums, 4, 5)
	fmt.Println("slice:", nums, "len:", len(nums), "cap:", cap(nums))

	// Sub-slice shares backing array — mutating affects original until growth.
	sub := nums[1:3]
	sub[0] = 99
	fmt.Println("after sub-slice mutation:", nums)

	// Make pre-allocates capacity (avoid reallocation on append).
	buf := make([]int, 0, 1000)
	for i := 0; i < 5; i++ {
		buf = append(buf, i)
	}
	fmt.Println("buf:", buf)

	// Map: hash table.
	ages := map[string]int{"asha": 30, "ravi": 25}
	ages["meera"] = 28
	if v, ok := ages["asha"]; ok {
		fmt.Println("asha is", v)
	}
	delete(ages, "ravi")
	for k, v := range ages {
		fmt.Println(k, v)
	}
}
