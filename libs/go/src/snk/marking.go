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

func (self *Marking) Eq (other *Marking) bool {
	if len(self.data) != len(other.data) {
		return false
	}
	for place, left := range self.data {
		if right, found := other.data[place] ; found {
			if ! left.Eq(right) {
				return false
			}
		} else {
			return false
		}
	}
	return true
}

//+++ snk.NewMarking().Eq(snk.NewMarking())

func (self *Marking) Set (place string, tokens ...interface{}) {
	self.data[place] = MakeMset(tokens...)
}

//### a := snk.NewMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... a.Println()
//... nil
//>>> set(eval(out).keys()) == {"p1", "p2"}
//>>> list(sorted(eval(out)["p1"])) == [1, 2, 2, 3]
//>>> list(sorted(eval(out)["p2"])) == [1, 1, 4]

func (self *Marking) Copy () *Marking {
	result := NewMarking()
	for key, value := range self.data {
		result.data[key] = value.Copy()
	}
	return result
}

//### a := snk.NewMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... b := snk.NewMarking()
//... b.Set("p1", 1, 2, 2, 3)
//... b.Set("p2", 1, 1, 4)
//... a.Eq(b)
//=== true

//### a := snk.NewMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... b := snk.NewMarking()
//... b.Set("p1", 1, 2, 2, 3)
//... b.Set("p3", 1, 1, 4)
//... a.Eq(b)
//=== false

//### a := snk.NewMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... b := snk.NewMarking()
//... b.Set("p1", 1, 2, 2, 3)
//... a.Eq(b)
//=== false

//### a := snk.NewMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... b := snk.NewMarking()
//... b.Set("p1", 1, 2, 2, 3)
//... b.Set("p2", 1, 1, 4)
//... b.Set("p3", 1)
//... a.Eq(b)
//=== false

//### a := snk.NewMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... b := snk.NewMarking()
//... b.Set("p1", 1, 2, 2, 3)
//... b.Set("p2", 1, 4)
//... a.Eq(b)
//=== false

func (self *Marking) Get (place string) *Mset {
	if value, found := self.data[place] ; found {
		return value
	} else {
		return NewMset()
	}
}

//### a := snk.NewMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... a.Get("p1").Eq(snk.MakeMset(1, 2, 2, 3))
//=== true

//### a := snk.NewMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... a.Get("p2").Eq(snk.MakeMset(1, 1, 4))
//=== true

//### a := snk.NewMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... a.Get("p3").Eq(snk.NewMset())
//=== true

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

//### a := snk.NewMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... a.NotEmpty("p1")
//=== true

//### a := snk.NewMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... a.NotEmpty("p1", "p2")
//=== true

//### a := snk.NewMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... a.NotEmpty("p1", "p2", "p3")
//=== false

//### a := snk.NewMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... a.NotEmpty("p3")
//=== false

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
