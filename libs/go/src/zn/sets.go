package zn

import "dicts"

type Set struct {
	d *dicts.Dict
}

type _z struct {
}

func (self _z) Hash () uint64 {
	return 8806599771745799646
}

func (self _z) Eq (other interface{}) bool {
	_, ok := other.(_z)
	if ok {
		return true
	} else {
		return false
	}
}

//*** a := zn.MakeMarking()
//*** a.Set("p1", 1)
//*** b := a.Copy()
//*** b.Set("p2", 2)
//*** c := b.Copy()
//*** c.Set("p3", 3)

func MakeSet (markings ...Marking) Set {
	dict := dicts.MakeDict()
	for _, m := range markings {
		dict.Set(m, _z{})
	}
	return Set{&dict}
}

func (self Set) Empty () bool {
	return self.d.Len() == 0
}

func (self Set) NotEmpty () bool {
	return self.d.Len() > 0
}

//+++ zn.MakeSet().Empty()
//--- zn.MakeSet(a).Empty()
//--- zn.MakeSet().NotEmpty()
//+++ zn.MakeSet(a).NotEmpty()

func (self Set) Len () uint64 {
	return self.d.Len()
}

//+++ zn.MakeSet().Len() == 0
//+++ zn.MakeSet(a).Len() == 1
//+++ zn.MakeSet(a, a).Len() == 1

func (self *Set) Add (m Marking) {
	self.d.Set(m, _z{})
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
	i := self.d.GetItem(m)
	if i == nil {
		return false, Marking{nil, -1}
	} else {
		return true, (*(i.Key)).(Marking)
	}
}

//### x := a.Copy()
//... x.SetId(42)
//... s := zn.MakeSet(x, b)
//... s.Get(a)
//=== true [42] {"p1": [1]}

func (self Set) Has (m Marking) bool {
	return self.d.Has(m)
}

//+++ zn.MakeSet(a, b).Has(a)
//+++ zn.MakeSet(a, b).Has(b)
//--- zn.MakeSet(a, b).Has(c)

type SetIterator struct {
	i dicts.DictIterator
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
	i, f := self.d.Iter()
	if f == nil {
		return SetIterator{i}, nil
	} else {
		m := (*(f.Key)).(Marking)
		return SetIterator{i}, &m
	}
}

//### a.SetId(1)
//... b.SetId(2)
//... c.SetId(3)
//... s := zn.MakeSet(a, b, c)
//... for i, m := s.Iter(); m != nil; m = i.Next() { fmt.Println(*m) }
//... nil
//=== [1] {"p1": [1]}
//=== [2] {"p1": [1], "p2": [2]}
//=== [3] {"p1": [1], "p2": [2], "p3": [3]}
