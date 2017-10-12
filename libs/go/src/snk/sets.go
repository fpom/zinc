package snk

import "fmt"

type Set struct {
	data map[interface{}]bool
}

func NewSet() *Set {
	return &Set{
		data: map[interface{}]bool{},
	}
}

func MakeSet(i ...interface{}) *Set {
	data := make(map[interface{}]bool)
	for _, e := range i {
		data[e] = true
	}
	return &Set{data: data}
}

func (self *Set) Len () int {
	return len(self.data)
}

func (self *Set) Pop () interface{} {
	for key, value := range self.data {
		delete(self.data, key)
		if value {
			return key
		}
	}
	return nil
}

func (self *Set) Has (val interface{}) bool {
	a, b := self.data[val]
	return b && a
}

func (self *Set) Iter () <-chan interface{} {
	ch := make(chan interface{})
    go func() {
        for key, _ := range self.data {
            ch <- key
        }
        close(ch)
    }()
    return ch
}

func (self *Set) Copy () *Set {
	result := NewSet()
	for key, value := range self.data {
		if value {
			result.data[key] = value
		}
	}
	return result
}

func (self *Set) Remove (other *Set) *Set {
	for key, value := range other.data {
		if _, found := self.data[key]; value && found {
			delete(self.data, key)
		}
	}
	return self
}

func (self *Set) Update (other *Set) *Set {
	for key, value := range other.data {
		self.data[key] = value
	}
	return self
}

func (self *Set) Add (value interface{}) *Set {
	self.data[value] = true
	return self
}

func (self *Set) Empty () bool {
	return len(self.data) == 0
}

func (self *Set) Print () {
	count := 0
	fmt.Print("{")
	for key, _ := range self.data {
		count += 1
		fmt.Print(key)
		if count < len(self.data) {
			fmt.Print(", ")
		}
	}	
	fmt.Print("}")
}

func (self *Set) Println () {
	self.Print()
	fmt.Println()
}
