// Standard library testing with table-driven tests.
// Save in *_test.go and run:  go test -v ./...
package main

// Example function to test.
func Add(a, b int) int { return a + b }

func main() {}

// --- in add_test.go ---
//
// package main
//
// import "testing"
//
// func TestAdd(t *testing.T) {
//     cases := []struct{ name string; a, b, want int }{
//         {"two_positives", 1, 2, 3},
//         {"with_negative", -1, 5, 4},
//         {"zero", 0, 0, 0},
//     }
//     for _, c := range cases {
//         c := c
//         t.Run(c.name, func(t *testing.T) {
//             if got := Add(c.a, c.b); got != c.want {
//                 t.Errorf("Add(%d,%d)=%d want %d", c.a, c.b, got, c.want)
//             }
//         })
//     }
// }
//
// func BenchmarkAdd(b *testing.B) {
//     for i := 0; i < b.N; i++ {
//         Add(1, 2)
//     }
// }
