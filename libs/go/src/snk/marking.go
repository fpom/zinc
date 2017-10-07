package snk

import "fmt"

type Marking struct {
	data map[string]*Mset
}

func NewMarking() *Marking {
	return &Marking{
		data: make(map[string]*Mset),
	}
}

func (self *Marking) Set (place string, tokens ...interface{}) {
	self.data[place] = MakeMset(tokens...)
}

func (self *Marking) Copy () *Marking {
	result := NewMarking()
	for key, value := range self.data {
		result.data[key] = value.Copy()
	}
	return result
}

func (self *Marking) Get (place string) *Mset {
	if value, found := self.data[place] ; found {
		return value
	} else {
		return NewMset()
	}
}

func (self *Marking) NotEmpty (places ...string) bool {
	for _, key := range places {
		if value, found := self.data[key] ; found {
			if value.Empty() {
				return false
			}
		} else {
			return false
		}
	}
	return true
}

func (self *Marking) Add (other *Marking) *Marking {
	for key, more := range other.data {
		if value, found := self.data[key] ; found {
			value.Add(more)
		} else {
			self.data[key] = more.Copy()
		}
	}
	return self
}

func (self *Marking) Sub (other *Marking) *Marking {
	for key, value := range other.data {
		if more, found := self.data[key] ; found {
			value.Sub(more)
			if value.Empty() {
				delete(self.data, key)
			}
		}
	}
	return self
}

func (self *Marking) Iter (place string) <-chan interface{} {
	ch := make(chan interface{})
    go func() {
        for val, _ := range self.data[place].data {
            ch <- val
        }
        close(ch)
    }()
    return ch
}

func (self *Marking) Println () {
	for key, value := range self.data {
		fmt.Print(key, " => ")
		value.Println()
	}	
}
