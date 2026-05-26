// Repository: abstract data access behind an interface.
// Enables swapping persistence (in-memory for tests, Postgres for prod) without touching business logic.
package main

import (
	"errors"
	"fmt"
	"sync"
)

type User struct {
	ID   int
	Name string
}

type UserRepo interface {
	Get(id int) (*User, error)
	Save(u *User) error
}

type inMemoryRepo struct {
	mu    sync.RWMutex
	store map[int]*User
}

func NewMemRepo() *inMemoryRepo { return &inMemoryRepo{store: map[int]*User{}} }

func (r *inMemoryRepo) Get(id int) (*User, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()
	if u, ok := r.store[id]; ok {
		return u, nil
	}
	return nil, errors.New("not found")
}

func (r *inMemoryRepo) Save(u *User) error {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.store[u.ID] = u
	return nil
}

type Service struct{ repo UserRepo }

func (s *Service) Welcome(id int) string {
	u, err := s.repo.Get(id)
	if err != nil {
		return "stranger"
	}
	return "welcome " + u.Name
}

func main() {
	repo := NewMemRepo()
	_ = repo.Save(&User{ID: 1, Name: "Asha"})
	s := &Service{repo: repo}
	fmt.Println(s.Welcome(1))
	fmt.Println(s.Welcome(2))
}
