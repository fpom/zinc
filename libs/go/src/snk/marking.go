package snk

import "fmt"

type Marking map[string]Mset

func (self Marking) Eq (other Marking) bool {
	if len(self) != len(other) {
		return false
	}
	for place, left := range self {
		if right, found := other[place] ; found {
			if ! left.Eq(right) {
				return false
			}
		} else {
			return false
		}
	}
	return true
}

//+++ snk.Marking{}.Eq(snk.Marking{})

func (self Marking) Set (place string, tokens ...interface{}) {
	self[place] = MakeMset(tokens...)
}

//### a := snk.Marking{}
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... a.Println()
//... nil
//>>> assign(m=eval(out))
//>>> set(m) == {"p1", "p2"}
//>>> list(sorted(m["p1"])) == [1, 2, 2, 3]
//>>> list(sorted(m["p2"])) == [1, 1, 4]

func (self Marking) Copy () Marking {
	copy := Marking{}
	for key, value := range self {
		copy[key] = value.Copy()
	}
	return copy
}

//### a := snk.Marking{}
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... b := snk.Marking{}
//... b.Set("p1", 1, 2, 2, 3)
//... b.Set("p2", 1, 1, 4)
//... a.Eq(b)
//=== true

//### a := snk.Marking{}
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... b := snk.Marking{}
//... b.Set("p1", 1, 2, 2, 3)
//... b.Set("p3", 1, 1, 4)
//... a.Eq(b)
//=== false

//### a := snk.Marking{}
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... b := snk.Marking{}
//... b.Set("p1", 1, 2, 2, 3)
//... a.Eq(b)
//=== false

//### a := snk.Marking{}
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... b := snk.Marking{}
//... b.Set("p1", 1, 2, 2, 3)
//... b.Set("p2", 1, 1, 4)
//... b.Set("p3", 1)
//... a.Eq(b)
//=== false

//### a := snk.Marking{}
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... b := snk.Marking{}
//... b.Set("p1", 1, 2, 2, 3)
//... b.Set("p2", 1, 4)
//... a.Eq(b)
//=== false

func (self Marking) Get (place string) Mset {
	if value, found := self[place] ; found {
		return value
	} else {
		return Mset{}
	}
}

//### a := snk.Marking{}
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... a.Get("p1").Eq(snk.MakeMset(1, 2, 2, 3))
//=== true

//### a := snk.Marking{}
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... a.Get("p2").Eq(snk.MakeMset(1, 1, 4))
//=== true

//### a := snk.Marking{}
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... a.Get("p3").Eq(snk.Mset{})
//=== true

func (self Marking) NotEmpty (places ...string) bool {
	for _, key := range places {
		if value, found := self[key] ; found {
			if value.Empty() {
				return false
			}
		} else {
			return false
		}
	}
	return true
}

//### a := snk.Marking{}
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... a.NotEmpty("p1")
//=== true

//### a := snk.Marking{}
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... a.NotEmpty("p1", "p2")
//=== true

//### a := snk.Marking{}
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... a.NotEmpty("p1", "p2", "p3")
//=== false

//### a := snk.Marking{}
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... a.NotEmpty("p3")
//=== false

func (self Marking) Add (other Marking) Marking {
	for place, right := range other {
		if left, found := self[place] ; found {
			left.Add(right)
		} else {
			self[place] = right.Copy()
		}
	}
	return self
}

//### a := snk.Marking{}
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... b := snk.Marking{}
//... b.Set("p2", 2, 4)
//... b.Set("p3", 1)
//... c := snk.Marking{}
//... c.Set("p1", 1, 2, 2, 3)
//... c.Set("p2", 1, 1, 2, 4, 4)
//... c.Set("p3", 1)
//... a.Add(b)
//... a.Eq(c)
//=== true

func (self Marking) Sub (other Marking) Marking {
	for place, right := range other {
		if left, found := self[place] ; found {
			left.Sub(right)
			if left.Empty() {
				delete(self, place)
			}
		}
	}
	return self
}

//### a := snk.Marking{}
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... b := snk.Marking{}
//... b.Set("p1", 1, 2, 2, 3)
//... b.Set("p2", 2, 4)
//... b.Set("p3", 1)
//... c := snk.Marking{}
//... c.Set("p2", 1, 1)
//... a.Sub(b)
//... a.Eq(c)
//=== true

func (self Marking) Geq (other Marking) bool {
	for key, value := range other {
		if mine, found := self[key] ; found {
			if ! mine.Geq(value) {
				return false
			}
		} else {
			return false
		}
	}
	return true
}

//### a := snk.Marking{}
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... b := snk.Marking{}
//... b.Set("p1", 1, 2, 2, 3)
//... b.Set("p2", 1, 1, 4)
//... a.Geq(b)
//=== true

//### a := snk.Marking{}
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... b := snk.Marking{}
//... b.Set("p1", 1, 2, 2, 3)
//... b.Set("p2", 1)
//... a.Geq(b)
//=== true

//### a := snk.Marking{}
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... b := snk.Marking{}
//... b.Set("p1", 1, 2, 2, 3)
//... a.Geq(b)
//=== true

//### a := snk.Marking{}
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... b := snk.Marking{}
//... b.Set("p1", 1, 2, 2, 3)
//... b.Set("p2", 1, 1, 1, 1)
//... a.Geq(b)
//=== false

//### a := snk.Marking{}
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... b := snk.Marking{}
//... b.Set("p1", 1, 2, 2, 3)
//... b.Set("p2", 1, 1, 4)
//... b.Set("p3", 1)
//... a.Geq(b)
//=== false

func (self Marking) Iter (place string) <-chan interface{} {
	ch := make(chan interface{})
    go func() {
		_, found := self[place]
		if found {
			for val, _ := range self[place] {
				ch <- val
			}
		}
        close(ch)
    }()
    return ch
}

//### a := snk.Marking{}
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... fmt.Print("{")
//... for i := range a.Iter("p1") { fmt.Print(i, ", ") }
//... fmt.Println("}")
//... nil
//>>> eval(out) == {1, 2, 3}

//### a := snk.Marking{}
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... fmt.Print("{")
//... for i := range a.Iter("p3") { fmt.Print(i, ", ") }
//... fmt.Println("}")
//... nil
//=== {}

func (self Marking) Println () {
	i := 0
	fmt.Print("{")
	for key, value := range self {
		if i > 0 {
			fmt.Print(", ")
		}
		i += 1
		fmt.Print(`"`, key, `": `)
		value.Print()
	}	
	fmt.Println("}")
}
