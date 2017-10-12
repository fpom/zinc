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
	for place, right := range other.data {
		if left, found := self.data[place] ; found {
			left.Add(right)
		} else {
			self.data[place] = right.Copy()
		}
	}
	return self
}

func (self *Marking) Sub (other *Marking) *Marking {
	for place, right := range other.data {
		if left, found := self.data[place] ; found {
			left.Sub(right)
			if left.Empty() {
				delete(self.data, place)
			}
		}
	}
	return self
}

func (self *Marking) Geq (other *Marking) bool {
	for key, value := range other.data {
		if mine, found := self.data[key] ; found {
			if ! mine.Geq(value) {
				return false
			}
		} else {
			return false
		}
	}
	return true
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
	i := 0
	fmt.Print("{")
	for key, value := range self.data {
		if i > 0 {
			fmt.Print(", ")
		}
		i += 1
		fmt.Print(`"`, key, `": `)
		value.Print()
	}	
	fmt.Println("}")
}
