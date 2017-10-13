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

func (self *Mset) Eq (other *Mset) bool {
	if len(self.data) != len(other.data) {
		return false
	}
	for key, left := range self.data {
		if right, found := other.data[key]; found {
			if left != right {
				return false
			}
		} else {
			return false
		}
	}
	return true
}

//+++ snk.NewMset().Eq(snk.MakeMset())
//--- snk.NewMset().Eq(snk.MakeMset(1, 2, 3))
//--- snk.NewMset().Eq(snk.MakeMset(1, 1, 1))
//+++ snk.MakeMset(1, 1, 1).Eq(snk.MakeMset(1, 1, 1))
//--- snk.MakeMset(1, 1, 3).Eq(snk.MakeMset(1, 1, 1))
//--- snk.MakeMset(1, 1, 1).Eq(snk.MakeMset(2, 2, 2))

func (self *Mset) Copy () *Mset {
	result := NewMset()
	for key, value := range self.data {
		result.data[key] = value
	}
	return result
}

//+++ snk.MakeMset(1, 2, 2, 3, 3, 3).Copy().Eq(snk.MakeMset(1, 2, 2, 3, 3, 3))

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

//### a := snk.MakeMset(1, 2, 3)
//... b := snk.MakeMset(2, 3, 4)
//... a.Add(b)
//... a.Eq(snk.MakeMset(1, 2, 2, 3, 3, 4))
//=== true

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

//### a := snk.MakeMset(1, 2, 3)
//... b := snk.MakeMset(2, 3, 4)
//... a.Sub(b)
//... a.Eq(snk.MakeMset(1))
//=== true

//### a := snk.MakeMset(1, 2, 2, 3, 3, 3)
//... b := snk.MakeMset(1, 2, 3)
//... a.Sub(b)
//... a.Eq(snk.MakeMset(2, 3, 3))
//=== true

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

//+++ snk.MakeMset(1, 2, 3).Geq(snk.MakeMset(1, 2, 3))
//+++ snk.MakeMset(1, 2, 3).Geq(snk.MakeMset(1, 2))
//+++ snk.MakeMset(1, 2, 2, 3).Geq(snk.MakeMset(1, 2, 3))
//+++ snk.MakeMset(1, 2, 2, 3).Geq(snk.NewMset())
//+++ snk.NewMset().Geq(snk.NewMset())
//--- snk.MakeMset(1, 2, 2, 3).Geq(snk.MakeMset(1, 2, 3, 4))
//--- snk.MakeMset(1, 2, 3).Geq(snk.MakeMset(1, 2, 2, 3))
//--- snk.NewMset().Geq(snk.MakeMset(1))

func (self *Mset) Empty () bool {
	return len(self.data) == 0
}

//+++ snk.NewMset().Empty()
//+++ snk.MakeMset().Empty()
//--- snk.MakeMset(1, 2).Empty()

func (self *Mset) Count (value interface{}) int {
	if count, found := self.data[value] ; found {
		return count
	} else {
		return 0
	}
}

//### snk.MakeMset(1, 2, 2, 3, 3, 3).Count(1)
//=== 1

//### snk.MakeMset(1, 2, 2, 3, 3, 3).Count(2)
//=== 2

//### snk.MakeMset(1, 2, 2, 3, 3, 3).Count(3)
//=== 3

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

//### a := snk.MakeMset(1, 2, 2, 3, 3, 3)
//... t := 0
//... for n := range a.Iter() { t += n.(int) }
//... t
//=== 6

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

//### a := snk.MakeMset(1, 2, 3)
//... a.Println()
//... nil
//>>> list(sorted((eval(out)))) == [1, 2, 3]

//### a := snk.MakeMset(1, 2, 2, 3, 3, 3)
//... a.Println()
//... nil
//>>> list(sorted(eval(out))) == [1, 2, 2, 3, 3, 3]
