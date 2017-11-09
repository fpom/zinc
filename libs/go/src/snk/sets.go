package snk

import "hashstructure"

type Set struct {
	data map[uint64]Marking
}

func NewSet () Set {
	return Set{make(map[uint64]Marking)}
}

//*** a := snk.NewMarking()
//*** a.Set("p1", 1)
//*** b := a.Copy()
//*** b.Set("p2", 2)
//*** c := b.Copy()
//*** c.Set("p3", 3)

func MakeSet (markings ...Marking) Set {
	set := NewSet()
	for _, m := range markings {
		set.Add(m)
	}
	return set
}

//### m := snk.MakeSet(a, b, c)
//... m.Eq(snk.MakeSet(c, b, a))
//=== true

//### m := snk.MakeSet(a, b, c)
//... m.Eq(snk.MakeSet(b, c, a))
//=== true

//### m := snk.MakeSet(a, b, c, a, b, c)
//... m.Eq(snk.MakeSet(b, c, a.Copy()))
//=== true

//### m := snk.MakeSet(a, b, c)
//... m.Eq(snk.MakeSet(b, c))
//=== false

func (self Set) Empty () bool {
	return len(self.data) == 0
}

func (self Set) NotEmpty () bool {
	return len(self.data) > 0
}

//+++ snk.NewSet().Empty()
//--- snk.MakeSet(snk.NewMarking()).Empty()
//--- snk.NewSet().NotEmpty()
//+++ snk.MakeSet(snk.NewMarking()).NotEmpty()

func (self Set) Len () int {
	return len(self.data)
}

//+++ snk.NewSet().Len() == 0
//+++ snk.MakeSet(snk.NewMarking()).Len() == 1
//+++ snk.MakeSet(snk.NewMarking(), snk.NewMarking()).Len() == 1

func (self Set) lookup (m Marking) (uint64, bool) {
	slot, err := hashstructure.Hash(m.data, nil)
	if err != nil {
		panic(err)
	}
	perturb := slot
	for true {
		if value, found := self.data[slot]; !found {
			return slot, false
		} else if value.Eq(m) {
			return slot, true
		} else {
			slot = (5 * slot) + 1 + perturb
			perturb >>= 5
		}
	}
	return 0, false
}

func (self Set) Add (m Marking) Set {
	if slot, found := self.lookup(m); !found {
		self.data[slot] = m
	}
	return self
}

//### s := snk.MakeSet(a, b)
//... s.Len()
//=== 2

//### s := snk.MakeSet(a, b)
//... s.Add(c).Add(c)
//... s.Len()
//=== 3

func (self Set) Discard (m Marking) Set {
	if slot, found := self.lookup(m); found {
		delete(self.data, slot)
	}
	return self
}

//### s := snk.MakeSet(a, b, c)
//... s.Discard(a).Discard(b).Discard(c)
//... s.Println()
//... s.Empty()
//=== true

func (self Set) Pop () Marking {
	for key, value := range self.data {
		delete(self.data, key)
		return value
	}
	panic("empty set")
}

//### s := snk.MakeSet(a)
//... s.Pop().Eq(a)
//=== true

//### s := snk.MakeSet(a)
//... s.Pop().Eq(b)
//=== false

//### s := snk.MakeSet(a, b)
//... x, y := s.Pop(), s.Pop()
//... ((x.Eq(a) && y.Eq(b)) || (x.Eq(b) && y.Eq(a))) && s.Empty()
//=== true

func (self Set) Has (m Marking) bool {
	_, found := self.lookup(m)
	return found
}

//+++ snk.MakeSet(a, b).Has(a)
//+++ snk.MakeSet(a, b).Has(b)
//--- snk.MakeSet(a, b).Has(c)

type SetIterator struct {
	done bool
	ask chan bool
	rep chan *Marking
}

func (self SetIterator) Next () *Marking {
	var rep *Marking
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

func (self SetIterator) Stop() {
	if ! self.done {
		self.ask <- false
		self.done = true
	}
}

func (self Set) iterate (it SetIterator) {
	for _, m := range self.data {
		if it.done {
			return
		}
		if <- it.ask {
			it.rep <- &m
		} else {
			return
		}
	}
	if <- it.ask {
		it.rep <- nil
	}
}

func (self Set) Iter () (SetIterator, *Marking) {
	it := SetIterator{false, make(chan bool), make(chan *Marking)}
	go self.iterate(it)
	return it, it.Next()
}

//### s := snk.MakeSet(a, b, c)
//... for i, p := s.Iter(); p != nil; p = i.Next() {
//...   s.Add(*p)
//... }
//... s.Eq(snk.MakeSet(a, b, c))
//=== true

func (self Set) Copy () Set {
	copy := NewSet()
	for key, value := range self.data {
		copy.data[key] = value
	}
	return copy
}

//### s := snk.MakeSet(a, b, c)
//... q := s.Copy()
//... s.Eq(q)
//=== true

func (self Set) Eq (other Set) bool {
	if len(self.data) != len(other.data) {
		return false
	}
	for _, value := range other.data {
		if _, found := self.lookup(value); ! found {
			return false
		}
	}
	return true	
}

func (self Set) Remove (other Set) Set {
	for _, value := range other.data {
		if slot, found := self.lookup(value); found {
			delete(self.data, slot)
		}
	}
	return self
}

//### s := snk.MakeSet(a, b, c)
//... s.Remove(snk.MakeSet(a, b))
//... s.Eq(snk.MakeSet(c))
//=== true

func (self Set) Update (other Set) Set {
	for key, value := range other.data {
		self.data[key] = value
	}
	return self
}

//### s := snk.MakeSet(a)
//... s.Update(snk.MakeSet(b, c))
//... s.Eq(snk.MakeSet(a, b, c))
//=== true

//### s := snk.MakeSet(a, b)
//... s.Update(snk.MakeSet(b, c))
//... s.Eq(snk.MakeSet(a, b, c))
//=== true

func (self Set) Println () {
	for _, m := range self.data {
		m.Println()
	}	
}
