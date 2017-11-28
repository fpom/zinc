package snk

import "fmt"
import "bytes"
import "hash/fnv"
import "dicts"

type Marking struct {
	d *dicts.Dict
	i int
}

func (self *Marking) SetId (id int) {
	self.i = id
}

func MakeMarking (id ...int) Marking {
	d := dicts.MakeDict()
	if len(id) == 0 {
		return Marking{&d, -1}
	} else if len(id) == 1 {
		return Marking{&d, id[0]}
	} else {
		panic("at most one id expected")
	}
}

func (self Marking) Hash () uint64 {
	var h uint64 = 2471033218594493899
	hash := fnv.New64()
	for iter, item := self.d.Iter(); item != nil; item = iter.Next() {
		hash.Reset()
		hash.Write([]byte(fmt.Sprintf("[%s]{%x}",
			fmt.Sprint(*(item.Key)),
			(*item.Value).(Mset).Hash())))
		h ^= hash.Sum64()
	}
	return h
}

type place struct {
	s string
}

func (self place) Hash () uint64 {
	return dicts.StringHash(self.s)
}

func (self place) Eq (other interface{}) bool {
	if val, isplace := other.(place); isplace {
		return val.s == self.s
	} else {
		return false
	}
}

func (self Marking) Has (p string) bool {
	return self.d.Has(place{p})
}

//### a := snk.MakeMarking()
//... a.Set("p1", 1, 2, 3, 4)
//... b := a.Copy()
//... b.Set("p2", 2, 3, 4, 5)
//... a.Hash() != b.Hash()
//=== true

//### a := snk.MakeMarking()
//... a.Set("p1", 1, 2, 3, 4)
//... b := a.Copy()
//... b.Set("p2")
//... a.Hash() == b.Hash()
//=== true

//### a := snk.MakeMarking()
//... a.Set("p1", 1, 2, 3, 4)
//... b := a.Copy()
//... b.Set("p2", 2, 3, 4, 5)
//... a.Set("p2", 5, 4, 3, 2)
//... a.Hash() == b.Hash()
//=== true

//### a := snk.MakeMarking()
//... a.Set("p1", 1, 2, 0)
//... a.Set("p2", 2, 1, 3)
//... a.Set("p3", 5, 6, 2)
//... b := snk.MakeMarking()
//... b.Set("p2", 1, 3, 2)
//... b.Set("p3", 2, 5, 6)
//... b.Set("p1", 2, 0, 1)
//... a.Hash() == b.Hash()
//=== true

func (self Marking) Eq (other Marking) bool {
	if self.d.Len() != other.d.Len() {
		return false
	}
	for iter, p, m := self.Iter(); p != nil; p, m = iter.Next() {
		if ! other.d.Has(place{*p}) {
			return false
		} else if ! m.Eq(other.Get(*p)) {
			return false
		}
	}
	return true
}

//+++ snk.MakeMarking().Eq(snk.MakeMarking())

func (self Marking) Set (p string, tokens ...interface{}) {
	if len(tokens) == 0 {
		self.d.Del(place{p})
	} else {
		m := MakeMset(tokens...)
		self.d.Set(place{p}, m)
	}
}

//### a := snk.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... a
//>>> assign(m=eval(out))
//>>> set(m) == {"p1", "p2"}
//>>> list(sorted(m["p1"])) == [1, 2, 2, 3]
//>>> list(sorted(m["p2"])) == [1, 1, 4]

//### a := snk.MakeMarking()
//... a.Set("p1", 1, 2)
//... a.Set("p1")
//... a.Get("p1").Empty()
//=== true

func (self Marking) Update (p string, tokens Mset) {
	if self.Has(p) {
		m := self.Get(p)
		m.Add(tokens)
	} else {
		self.d.Set(place{p}, tokens.Copy())
	}
}

//### a := snk.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Update("p1", snk.MakeMset(1, 2, 2, 3))
//... a.Update("p2", snk.MakeMset(1, 1, 4))
//... b := snk.MakeMarking()
//... b.Set("p1", 1, 2, 2, 3, 1, 2, 2, 3)
//... b.Set("p2", 1, 1, 4)
//... a.Eq(b)
//=== true

func (self Marking) Copy () Marking {
	copy := MakeMarking()
	for iter, p, m := self.Iter(); p != nil; p, m = iter.Next() {
		copy.Update(*p, *m)
	}
	return copy
}

//### a := snk.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... b := snk.MakeMarking()
//... b.Set("p1", 1, 2, 2, 3)
//... b.Set("p2", 1, 1, 4)
//... a.Eq(b)
//=== true

//### a := snk.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... b := snk.MakeMarking()
//... b.Set("p1", 1, 2, 2, 3)
//... b.Set("p3", 1, 1, 4)
//... a.Eq(b)
//=== false

//### a := snk.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... b := snk.MakeMarking()
//... b.Set("p1", 1, 2, 2, 3)
//... a.Eq(b)
//=== false

//### a := snk.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... b := snk.MakeMarking()
//... b.Set("p1", 1, 2, 2, 3)
//... b.Set("p2", 1, 1, 4)
//... b.Set("p3", 1)
//... a.Eq(b)
//=== false

//### a := snk.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... b := snk.MakeMarking()
//... b.Set("p1", 1, 2, 2, 3)
//... b.Set("p2", 1, 4)
//... a.Eq(b)
//=== false

func (self Marking) Get (p string) Mset {
	return (*(self.d.Fetch(place{p}, MakeMset()))).(Mset)
}

//### a := snk.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... a.Get("p1").Eq(snk.MakeMset(1, 2, 2, 3))
//=== true

//### a := snk.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... a.Get("p2").Eq(snk.MakeMset(1, 1, 4))
//=== true

//### a := snk.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... a.Get("p3").Eq(snk.MakeMset())
//=== true

func (self Marking) NotEmpty (places ...string) bool {
	for _, key := range places {
		if self.Get(key).Empty() {
			return false
		}
	}
	return true
}

//### a := snk.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... a.NotEmpty("p1")
//=== true

//### a := snk.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... a.NotEmpty("p1", "p2")
//=== true

//### a := snk.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... a.NotEmpty("p1", "p2", "p3")
//=== false

//### a := snk.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... a.NotEmpty("p3")
//=== false

func (self Marking) Add (other Marking) Marking {
	for iter, p, m := other.Iter(); p != nil; p, m = iter.Next() {
		self.Update(*p, *m)
	}
	return self
}

//### a := snk.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... b := snk.MakeMarking()
//... b.Set("p2", 2, 4)
//... b.Set("p3", 1)
//... a.Add(b)
//... c := snk.MakeMarking()
//... c.Set("p1", 1, 2, 2, 3)
//... c.Set("p2", 1, 1, 2, 4, 4)
//... c.Set("p3", 1)
//... a.Eq(c)
//=== true

func (self Marking) Sub (other Marking) Marking {
	for iter, p, m := other.Iter(); p != nil; p, m = iter.Next() {
		mine := self.Get(*p)
		if m.Geq(mine) {
			self.d.Del(place{*p})
		} else {
			mine.Sub(*m)
		}
	}
	return self
}

//### a := snk.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... b := snk.MakeMarking()
//... b.Set("p1", 1, 2, 2, 3)
//... b.Set("p2", 2, 4)
//... b.Set("p3", 1)
//... c := snk.MakeMarking()
//... c.Set("p2", 1, 1)
//... a.Sub(b)
//... a.Eq(c)
//=== true

func (self Marking) Geq (other Marking) bool {
	for iter, p, m := other.Iter(); p != nil; p, m = iter.Next() {
		if ! self.Get(*p).Geq(*m) {
			return false
		}
	}
	return true
}

//### a := snk.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... b := snk.MakeMarking()
//... b.Set("p1", 1, 2, 2, 3)
//... b.Set("p2", 1, 1, 4)
//... a.Geq(b)
//=== true

//### a := snk.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... b := snk.MakeMarking()
//... b.Set("p1", 1, 2, 2, 3)
//... b.Set("p2", 1)
//... a.Geq(b)
//=== true

//### a := snk.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... b := snk.MakeMarking()
//... b.Set("p1", 1, 2, 2, 3)
//... a.Geq(b)
//=== true

//### a := snk.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... b := snk.MakeMarking()
//... b.Set("p1", 1, 2, 2, 3)
//... b.Set("p2", 1, 1, 1, 1)
//... a.Geq(b)
//=== false

//### a := snk.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... b := snk.MakeMarking()
//... b.Set("p1", 1, 2, 2, 3)
//... b.Set("p2", 1, 1, 4)
//... b.Set("p3", 1)
//... a.Geq(b)
//=== false

type MarkingIterator struct {
	iter *dicts.DictIterator
}

func (self MarkingIterator) Next () (*string, *Mset) {
	next := self.iter.Next()
	if next == nil {
		return nil, nil
	} else {
		p := (*next.Key).(place)
		m := (*next.Value).(Mset)
		return &(p.s),  &m
	}
}

func (self Marking) Iter () (MarkingIterator, *string, *Mset) {
	iter, item := self.d.Iter()
	myiter := MarkingIterator{&iter}
	if item == nil {
		return myiter, nil, nil
	} else {
		p := (*item.Key).(place)
		m := (*item.Value).(Mset)
		return myiter, &(p.s), &m
	}
}

//### a := snk.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... fmt.Print("{")
//... for i, p := a.Get("p1").Iter(); p != nil; p = i.Next() { fmt.Print(*p, ", ") }
//... fmt.Println("}")
//... nil
//>>> eval(out) == {1, 2, 3}

//### a := snk.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... fmt.Print("{")
//... for i, p := a.Get("p3").Iter(); p != nil; p = i.Next() { fmt.Print(*p, ", ") }
//... fmt.Println("}")
//... nil
//=== {}

func (self Marking) String () string {
	buf := bytes.NewBufferString("")
	if self.i >= 0 {
		buf.WriteString(fmt.Sprintf("[%d] ", self.i))
	}
	buf.WriteString("{")
	comma := false
	for iter, p, m := self.Iter(); p != nil; p, m = iter.Next() {
		if comma {
			buf.WriteString(", ")
		} else {
			comma = true
		}
		buf.WriteString(fmt.Sprintf(`"%s": %s`, *p, *m))
	}	
	buf.WriteString("}")
	return buf.String()
}
