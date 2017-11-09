package snk

import "fmt"

type Mset struct {
	// hide map into a struct with unexported field
	data map[interface{}]int
}

func NewMset () Mset {
	return Mset{make(map[interface{}]int)}
}

func MakeMset (values ...interface{}) Mset {
	mset := NewMset()
	for _, elt := range values {
		if count, found := mset.data[elt]; found {
			mset.data[elt] = count + 1
		} else {
			mset.data[elt] = 1
		}
	}
	return mset
}

func (self Mset) Eq (other Mset) bool {
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

func (self Mset) Copy () Mset {
	copy := NewMset()
	for key, value := range self.data {
		copy.data[key] = value
	}
	return copy
}

//+++ snk.MakeMset(1, 2, 2, 3, 3, 3).Copy().Eq(snk.MakeMset(1, 2, 2, 3, 3, 3))

func (self Mset) Len () int {
	count := 0
	for _, value := range self.data {
		count += value
	}
	return count
}

//+++ snk.MakeMset(1, 2, 2, 3, 3, 3).Len() == 6
//+++ snk.NewMset().Len() == 0

func (self Mset) Mul (mul int) Mset {
	copy := NewMset()
	if mul <= 0 {
		return copy
	}
	for key, value := range self.data {
		copy.data[key] = value * mul
	}
	return copy	
}

//+++ snk.MakeMset(1, 2, 2).Mul(2).Eq(snk.MakeMset(1, 1, 2, 2, 2, 2))

func (self Mset) Add (other Mset) Mset {
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

func (self Mset) Sub (other Mset) Mset {
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

func (self Mset) Geq (other Mset) bool {
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

func (self Mset) Empty () bool {
	return len(self.data) == 0
}

//+++ snk.NewMset().Empty()
//+++ snk.MakeMset().Empty()
//--- snk.MakeMset(1, 2).Empty()

func (self Mset) Count (value interface{}) int {
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

type MsetIterator struct {
	done bool
	ask chan bool
	rep chan *interface{}
}

func (self MsetIterator) Next() *interface{} {
	var rep *interface{}
	if self.done {
		return nil
	}
	self.ask <- true
	rep = <- self.rep
	if rep == nil {
		self.done = true
	}
	return rep
}

func (self MsetIterator) Stop() {
	if ! self.done {
		self.ask <- false
		self.done = true
	}
}

func (self Mset) iterate (it MsetIterator, dup bool) {
	for key, num := range self.data {
		if !dup {
			num = 1
		}
		for i := 0; i < num; i++ {
			if it.done {
				return
			}
			if <- it.ask {
				it.rep <- &key
			} else {
				return
			}
		}
	}
	if <- it.ask {
		it.rep <- nil
	}
}

func (self Mset) Iter () (MsetIterator, *interface{}) {
	it := MsetIterator{false, make(chan bool), make(chan *interface{})}
	go self.iterate(it, false)
	return it, it.Next()
}

func (self Mset) IterDup () (MsetIterator, *interface{}) {
	it := MsetIterator{false, make(chan bool), make(chan *interface{})}
	go self.iterate(it, true)
	return it, it.Next()
}

//### a := snk.MakeMset(1, 2, 2, 3, 3, 3)
//... t := 0
//... for i, n := a.Iter(); n != nil; n = i.Next() { t += (*n).(int) }
//... t
//=== 6

//### a := snk.MakeMset(1, 2, 2, 3, 3, 3)
//... t := 0
//... for i, n := a.IterDup(); n != nil; n = i.Next() { t += (*n).(int) }
//... t
//=== 14

func (self Mset) Print () {
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

type mapfunc func (interface{}, int) (interface{}, int)

func (self Mset) Map (f mapfunc) Mset {
	copy := NewMset()
	for k0, n0 := range self.data {
		k1, n1 := f(k0, n0)
		copy.data[k1] = n1
	}
	return copy
}

//### a := snk.MakeMset(1, 2, 2)
//... b := a.Map(func (v interface{}, n int) (interface{}, int) {return v.(int)+1, n})
//... b.Eq(snk.MakeMset(2, 3, 3))
//=== true
