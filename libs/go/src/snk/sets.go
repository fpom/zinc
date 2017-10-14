package snk

import "hashstructure" 

type Set map[uint64]Marking

//*** a := snk.Marking{}
//*** a.Set("p1", 1)
//*** b := a.Copy()
//*** b.Set("p2", 2)
//*** c := b.Copy()
//*** c.Set("p3", 3)

func MakeSet (markings ...Marking) Set {
	set := Set{}
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
	return len(self) == 0
}

//+++ snk.Set{}.Empty()
//--- snk.MakeSet(snk.Marking{}).Empty()

func (self Set) Len () int {
	return len(self)
}

//+++ snk.Set{}.Len() == 0
//+++ snk.MakeSet(snk.Marking{}).Len() == 1
//+++ snk.MakeSet(snk.Marking{}, snk.Marking{}).Len() == 1

func (self Set) lookup (m Marking) (uint64, bool) {
	slot, err := hashstructure.Hash(m, nil)
	if err != nil {
		panic(err)
	}
	perturb := slot
	for true {
		if value, found := self[slot]; !found {
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

func (self Set) Add (m Marking) {
	slot, found := self.lookup(m)
	if ! found {
		self[slot] = m
	}
}

//### s := snk.MakeSet(a, b)
//... s.Len()
//=== 2

//### s := snk.MakeSet(a, b)
//... s.Add(c)
//... s.Add(c)
//... s.Len()
//=== 3

func (self Set) Discard (m Marking) Set {
	slot, found := self.lookup(m)
	if found {
		delete(self, slot)
	}
	return self
}

//### s := snk.MakeSet(a, b, c)
//... s.Discard(a).Discard(b).Discard(c)
//... s.Println()
//... s.Empty()
//=== true

func (self Set) Pop () Marking {
	for key, value := range self {
		delete(self, key)
		if value == nil {
			panic("nil Marking in Set")
		}
		return value
	}
	return nil
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

func (self Set) Iter () <-chan Marking {
	ch := make(chan Marking)
    go func() {
        for _, m := range self {
			if m == nil {
				panic("nil Marking in Set")
			}
			ch <- m
        }
        close(ch)
    }()
    return ch
}

//### s := snk.MakeSet(a, b, c)
//... for m := range s.Iter() {
//...   s.Add(m)
//... }
//... s.Eq(snk.MakeSet(a, b, c))
//=== true

func (self Set) Copy () Set {
	copy := Set{}
	for key, value := range self {
		if value == nil {
			panic("nil Marking in Set")
		}
		copy[key] = value
	}
	return copy
}

//### s := snk.MakeSet(a, b, c)
//... q := s.Copy()
//... s.Eq(q)
//=== true

func (self Set) Eq (other Set) bool {
	if len(self) != len(other) {
		return false
	}
	for _, value := range other {
		if value == nil {
			panic("nil Marking in Set")
		}
		if _, found := self.lookup(value); ! found {
			return false
		}
	}
	return true	
}

func (self Set) Remove (other Set) Set {
	for _, value := range other {
		if value == nil {
			panic("nil Marking in Set")
		}
		if slot, found := self.lookup(value); found {
			delete(self, slot)
		}
	}
	return self
}

//### s := snk.MakeSet(a, b, c)
//... s.Remove(snk.MakeSet(a, b))
//... s.Eq(snk.MakeSet(c))
//=== true

func (self Set) Update (other Set) Set {
	for key, value := range other {
		self[key] = value
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
	for _, m := range self {
		m.Println()
	}	
}
