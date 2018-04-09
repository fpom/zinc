package zn

import "fmt"
import "bytes"

type Marking struct {
	Id int
	h *Hashtable
}

func MakeMarking (id ...int) Marking {
	h := MakeHashtable(true)
	if len(id) == 0 {
		return Marking{-1, &h}
	} else if len(id) == 1 {
		return Marking{id[0], &h}
	} else {
		panic("at most one id expected")
	}
}

func (self *Marking) SetId (id int) {
	self.Id = id
}

func (self Marking) GetId () int {
	return self.Id
}

func (self Marking) Hash () uint64 {
	return self.h.Hash() + 8635519453209983077
}

func (self Marking) Eq (other interface{}) bool {
	m, ok := other.(Marking)
	if ok {
		return self.h == m.h || self.h.Eq(*(m.h))
	} else {
		return false
	}
}

func (self Marking) Has (p string) bool {
	return self.h.Has(p)
}

//### a := zn.MakeMarking()
//... a.Set("p1", 1, 2, 3, 4)
//... b := a.Copy()
//... b.Set("p2", 2, 3, 4, 5)
//... a.Hash() != b.Hash()
//=== true

//### a := zn.MakeMarking()
//... a.Set("p1", 1, 2, 3, 4)
//... b := a.Copy()
//... b.Set("p2")
//... a.Hash() == b.Hash()
//=== true

//### a := zn.MakeMarking()
//... a.Set("p1", 1, 2, 3, 4)
//... b := a.Copy()
//... b.Set("p2", 2, 3, 4, 5)
//... a.Set("p2", 5, 4, 3, 2)
//... a.Hash() == b.Hash()
//=== true

//### a := zn.MakeMarking()
//... a.Set("p1", 1, 2, 0)
//... a.Set("p2", 2, 1, 3)
//... a.Set("p3", 5, 6, 2)
//... b := zn.MakeMarking()
//... b.Set("p2", 1, 3, 2)
//... b.Set("p3", 2, 5, 6)
//... b.Set("p1", 2, 0, 1)
//... a.Hash() == b.Hash()
//=== true

//+++ zn.MakeMarking().Eq(zn.MakeMarking())

func (self Marking) Set (p string, tokens ...interface{}) {
	if len(tokens) == 0 {
		self.h.Del(p)
	} else {
		self.h.Put(p, MakeMset(tokens...))
	}
}

//### a := zn.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... a
//>>> assign(m=eval(out))
//>>> set(m) == {"p1", "p2"}
//>>> list(sorted(m["p1"])) == [1, 2, 2, 3]
//>>> list(sorted(m["p2"])) == [1, 1, 4]

//### a := zn.MakeMarking()
//... a.Set("p1", 1, 2)
//... a.Set("p1")
//... a.Get("p1").Empty()
//=== true

func (self Marking) Update (p string, tokens Mset) {
	k, m := self.h.Get(p)
	if k != nil {
		(*m).(Mset).Add(tokens)
	} else {
		self.h.Put(p, tokens.Copy())
	}
}

//### a := zn.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Update("p1", zn.MakeMset(1, 2, 2, 3))
//... a.Update("p2", zn.MakeMset(1, 1, 4))
//... b := zn.MakeMarking()
//... b.Set("p1", 1, 2, 2, 3, 1, 2, 2, 3)
//... b.Set("p2", 1, 1, 4)
//... a.Eq(b)
//=== true

func (self Marking) Copy () Marking {
	h := self.h.Copy()
	return Marking{self.Id, &h}
}

//### a := zn.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... b := zn.MakeMarking()
//... b.Set("p1", 1, 2, 2, 3)
//... b.Set("p2", 1, 1, 4)
//... a.Eq(b)
//=== true

//### a := zn.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... b := zn.MakeMarking()
//... b.Set("p1", 1, 2, 2, 3)
//... b.Set("p3", 1, 1, 4)
//... a.Eq(b)
//=== false

//### a := zn.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... b := zn.MakeMarking()
//... b.Set("p1", 1, 2, 2, 3)
//... a.Eq(b)
//=== false

//### a := zn.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... b := zn.MakeMarking()
//... b.Set("p1", 1, 2, 2, 3)
//... b.Set("p2", 1, 1, 4)
//... b.Set("p3", 1)
//... a.Eq(b)
//=== false

//### a := zn.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... b := zn.MakeMarking()
//... b.Set("p1", 1, 2, 2, 3)
//... b.Set("p2", 1, 4)
//... a.Eq(b)
//=== false

func (self Marking) Get (p string) Mset {
	k, m := self.h.Get(p)
	if k == nil {
		return MakeMset()
	} else {
		return (*m).(Mset)
	}
}

//### a := zn.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... a.Get("p1").Eq(zn.MakeMset(1, 2, 2, 3))
//=== true

//### a := zn.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... a.Get("p2").Eq(zn.MakeMset(1, 1, 4))
//=== true

//### a := zn.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... a.Get("p3").Eq(zn.MakeMset())
//=== true

func (self Marking) NotEmpty (places ...string) bool {
	for _, p := range places {
		k, m := self.h.Get(p)
		if k == nil {
			return false
		} else if (*m).(Mset).Empty() {
			return false
		}
	}
	return true
}

//### a := zn.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... a.NotEmpty("p1")
//=== true

//### a := zn.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... a.NotEmpty("p1", "p2")
//=== true

//### a := zn.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... a.NotEmpty("p1", "p2", "p3")
//=== false

//### a := zn.MakeMarking()
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

//### a := zn.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... b := zn.MakeMarking()
//... b.Set("p2", 2, 4)
//... b.Set("p3", 1)
//... a.Add(b)
//... c := zn.MakeMarking()
//... c.Set("p1", 1, 2, 2, 3)
//... c.Set("p2", 1, 1, 2, 4, 4)
//... c.Set("p3", 1)
//... a.Eq(c)
//=== true

func (self Marking) Sub (other Marking) Marking {
	for iter, place, right := other.Iter(); place != nil; place, right = iter.Next() {
		k, left := self.h.Get(*place)
		if k != nil {
			m := (*left).(Mset)
			if right.Geq(m) {
				self.h.Del(*place)
			} else {
				m.Sub(*right)
			}
		}
	}
	return self
}

//### a := zn.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... b := zn.MakeMarking()
//... b.Set("p1", 1, 2, 2, 3)
//... b.Set("p2", 2, 4)
//... b.Set("p3", 1)
//... c := zn.MakeMarking()
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

//### a := zn.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... b := zn.MakeMarking()
//... b.Set("p1", 1, 2, 2, 3)
//... b.Set("p2", 1, 1, 4)
//... a.Geq(b)
//=== true

//### a := zn.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... b := zn.MakeMarking()
//... b.Set("p1", 1, 2, 2, 3)
//... b.Set("p2", 1)
//... a.Geq(b)
//=== true

//### a := zn.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... b := zn.MakeMarking()
//... b.Set("p1", 1, 2, 2, 3)
//... a.Geq(b)
//=== true

//### a := zn.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... b := zn.MakeMarking()
//... b.Set("p1", 1, 2, 2, 3)
//... b.Set("p2", 1, 1, 1, 1)
//... a.Geq(b)
//=== false

//### a := zn.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... b := zn.MakeMarking()
//... b.Set("p1", 1, 2, 2, 3)
//... b.Set("p2", 1, 1, 4)
//... b.Set("p3", 1)
//... a.Geq(b)
//=== false

type MarkingIterator struct {
	iter HashtableIterator
}

func (self *MarkingIterator) Next () (*string, *Mset) {
	key, val := self.iter.Next()
	if key == nil {
		return nil, nil
	} else {
		p := (*key).(string)
		m := (*val).(Mset)
		return &p,  &m
	}
}

func (self Marking) Iter () (MarkingIterator, *string, *Mset) {
	iter, key, val := self.h.Iter()
	myiter := MarkingIterator{iter}
	if key == nil {
		return myiter, nil, nil
	} else {
		p := (*key).(string)
		m := (*val).(Mset)
		return myiter, &p, &m
	}
}

//### a := zn.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... fmt.Print("{")
//... for i, p := a.Get("p1").Iter(); p != nil; p = i.Next() { fmt.Print(*p, ", ") }
//... fmt.Println("}")
//... nil
//>>> eval(out) == {1, 2, 3}

//### a := zn.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... fmt.Print("{")
//... for i, p := a.Get("p3").Iter(); p != nil; p = i.Next() { fmt.Print(*p, ", ") }
//... fmt.Println("}")
//... nil
//=== {}

func (self Marking) String () string {
	buf := bytes.NewBufferString("")
	if self.Id >= 0 {
		buf.WriteString(fmt.Sprintf("[%d] %s", self.Id, *(self.h)))
	} else {
		buf.WriteString(fmt.Sprintf("%s", *(self.h)))
	}
	return buf.String()
}

//### a := zn.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... b := a.Copy()
//... b.Update("p1", zn.MakeMset(42))
//... a.Eq(b)
//=== false
