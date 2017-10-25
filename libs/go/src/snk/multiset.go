package snk

import "fmt"

type Mset map[interface{}]int

func MakeMset(values ...interface{}) Mset {
	mset := Mset{}
	for _, elt := range values {
		if count, found := mset[elt]; found {
			mset[elt] = count + 1
		} else {
			mset[elt] = 1
		}
	}
	return mset
}

func (self Mset) Eq (other Mset) bool {
	if len(self) != len(other) {
		return false
	}
	for key, left := range self {
		if right, found := other[key]; found {
			if left != right {
				return false
			}
		} else {
			return false
		}
	}
	return true
}

//+++ snk.Mset{}.Eq(snk.MakeMset())
//--- snk.Mset{}.Eq(snk.MakeMset(1, 2, 3))
//--- snk.Mset{}.Eq(snk.MakeMset(1, 1, 1))
//+++ snk.MakeMset(1, 1, 1).Eq(snk.MakeMset(1, 1, 1))
//--- snk.MakeMset(1, 1, 3).Eq(snk.MakeMset(1, 1, 1))
//--- snk.MakeMset(1, 1, 1).Eq(snk.MakeMset(2, 2, 2))

func (self Mset) Copy () Mset {
	copy := Mset{}
	for key, value := range self {
		copy[key] = value
	}
	return copy
}

//+++ snk.MakeMset(1, 2, 2, 3, 3, 3).Copy().Eq(snk.MakeMset(1, 2, 2, 3, 3, 3))

func (self Mset) Len () int {
	count := 0
	for _, value := range self {
		count += value
	}
	return count
}

//+++ snk.MakeMset(1, 2, 2, 3, 3, 3).Len() == 6
//+++ snk.Mset{}.Len() == 0

func (self Mset) Mul (mul int) Mset {
	copy := Mset{}
	if mul <= 0 {
		return copy
	}
	for key, value := range self {
		copy[key] = value * mul
	}
	return copy	
}

//+++ snk.MakeMset(1, 2, 2).Mul(2).Eq(snk.MakeMset(1, 1, 2, 2, 2, 2))

func (self Mset) Add (other Mset) Mset {
	for key, value := range other {
		if count, found := self[key] ; found {
			self[key] = value + count
		} else {
			self[key] = value
		}
	}
	return self
}

//### a := snk.MakeMset(1, 2, 3)
//... b := snk.MakeMset(2, 3, 4)
//... a.Add(b)
//... a.Eq(snk.MakeMset(1, 2, 2, 3, 3, 4))
//=== true

func (self Mset) Sub (other Mset) Mset {
	for key, value := range other {
		if count, found := self[key] ; found {
			if count > value {
				self[key] = count - value
			} else {
				delete(self, key)
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

func (self Mset) Geq (other Mset) bool {
	for key, value := range other {
		if count, found := self[key] ; found {
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
//+++ snk.MakeMset(1, 2, 2, 3).Geq(snk.Mset{})
//+++ snk.Mset{}.Geq(snk.Mset{})
//--- snk.MakeMset(1, 2, 2, 3).Geq(snk.MakeMset(1, 2, 3, 4))
//--- snk.MakeMset(1, 2, 3).Geq(snk.MakeMset(1, 2, 2, 3))
//--- snk.Mset{}.Geq(snk.MakeMset(1))

func (self Mset) Empty () bool {
	return len(self) == 0
}

//+++ snk.Mset{}.Empty()
//+++ snk.MakeMset().Empty()
//--- snk.MakeMset(1, 2).Empty()

func (self Mset) Count (value interface{}) int {
	if count, found := self[value] ; found {
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

func (self Mset) Iter () <-chan interface{} {
	ch := make(chan interface{})
    go func() {
        for key, _ := range self {
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

func (self Mset) Print () {
	count := 0
	fmt.Print("[")
	for key, value := range self {
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

func (self Mset) Println () {
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
