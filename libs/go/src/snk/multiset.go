package snk

import "fmt"

type Mset struct {
	data map[interface{}]int
}

func NewMset() *Mset {
	return &Mset{
		data: map[interface{}]int{},
	}
}

func MakeMset(i ...interface{}) *Mset {
	data := make(map[interface{}]int)
	for _, e := range i {
		if count, found := data[e]; found {
			data[e] = count + 1
		} else {
			data[e] = 1
		}
	}
	return &Mset{data: data}
}

func (self *Mset) Copy () *Mset {
	result := NewMset()
	for key, value := range self.data {
		result.data[key] = value
	}
	return result
}

func (self *Mset) Add (other *Mset) *Mset {
	for key, value := range other.data {
		if count, found := self.data[key] ; found {
			self.data[key] = value + count
		} else {
			self.data[key] = value
		}
	}
	return self
}

func (self *Mset) Sub (other *Mset) *Mset {
	for key, value := range other.data {
		if count, found := self.data[key] ; found {
			if count > value {
				self.data[key] = count - value
			} else {
				delete(self.data, key)
			}
		}
	}
	return self
}

func (self *Mset) Geq (other *Mset) bool {
	for key, value := range other.data {
		if count, found := self.data[key] ; found {
			if count < value {
				return false
			}
		} else {
			return false
		}
	}
	return true
}

func (self *Mset) Empty () bool {
	return len(self.data) == 0
}

func (self *Mset) Count (value interface{}) int {
	if count, found := self.data[value] ; found {
		return count
	} else {
		return 0
	}
}

func (self *Mset) Iter () <-chan interface{} {
	ch := make(chan interface{})
    go func() {
        for key, _ := range self.data {
            ch <- key
        }
        close(ch)
    }()
    return ch
}

func (self *Mset) Print () {
	count := 0
	fmt.Print("[")
	for key, value := range self.data {
		for i := 0; i < value; i += 1 {
			if count >  0 {
				fmt.Print(", ")
			}
			fmt.Print(key)
			count += 1
		}
	}	
	fmt.Print("]")
}

func (self *Mset) Println () {
	self.Print()
	fmt.Println()
}
