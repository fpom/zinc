package zn

import "dicts"

type Set struct {
	s *dicts.Set
}

//*** a := zn.MakeMarking()
//*** a.Set("p1", 1)
//*** b := a.Copy()
//*** b.Set("p2", 2)
//*** c := b.Copy()
//*** c.Set("p3", 3)

func MakeSet (markings ...Marking) Set {
	set := dicts.MakeSet()
	for _, m := range markings {
		set.Add(m)
	}
	return Set{&set}
}

func (self Set) Empty () bool {
	return self.s.Len() == 0
}

func (self Set) NotEmpty () bool {
	return self.s.Len() > 0
}

//+++ zn.MakeSet().Empty()
//--- zn.MakeSet(a).Empty()
//--- zn.MakeSet().NotEmpty()
//+++ zn.MakeSet(a).NotEmpty()

func (self Set) Len () uint64 {
	return self.s.Len()
}

//+++ zn.MakeSet().Len() == 0
//+++ zn.MakeSet(a).Len() == 1
//+++ zn.MakeSet(a, a).Len() == 1

func (self *Set) Add (m Marking) {
	self.s.Add(m)
}

//### s := zn.MakeSet(a, b)
//... s.Len()
//=== 2

//### s := zn.MakeSet(a, b)
//... s.Add(c)
//... s.Add(c)
//... s.Len()
//=== 3

func (self Set) Get (m Marking) (bool, Marking) {
	k := self.s.Get(m)
	if k == nil {
		return false, MakeMarking()
	} else {
		return true, (*k).(Marking)
	}
}

//### x := a.Copy()
//... x.Id = 42
//... s := zn.MakeSet(x, b)
//... s.Get(a)
//=== true [42] {"p1": [1]}

func (self Set) Has (m Marking) bool {
	return self.s.Has(m)
}

//+++ zn.MakeSet(a, b).Has(a)
//+++ zn.MakeSet(a, b).Has(b)
//--- zn.MakeSet(a, b).Has(c)

type SetIterator struct {
	i dicts.SetIterator
}

func (self *SetIterator) Next () *Marking {
	n := self.i.Next()
	if n == nil {
		return nil
	} else {
		m := (*(n.Key)).(Marking)
		return &m
	}
}

func (self Set) Iter () (SetIterator, *Marking) {
	i, f := self.s.Iter()
	if f == nil {
		return SetIterator{i}, nil
	} else {
		m := (*(f.Key)).(Marking)
		return SetIterator{i}, &m
	}
}

//### a.Id = 1
//... b.Id = 2
//... c.Id = 3
//... s := zn.MakeSet(a, b, c)
//... for i, m := s.Iter(); m != nil; m = i.Next() { fmt.Println((*m).Id) }
//... nil
//=== 1
//=== 2
//=== 3
