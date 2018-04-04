package zn

import "fmt"
import "bytes"
import "dicts"

type Marking struct {
	d *dicts.Dict
	i int
}

func (self *Marking) SetId (id int) {
	self.i = id
}

func (self Marking) GetId () int {
	return self.i
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
	return self.d.Hash()
}

func (self Marking) Eq (other interface{}) bool {
	m, ok := other.(Marking)
	if ok {
		return self.d.Eq(*(m.d))
	} else {
		return false
	}
}

func (self Marking) Has (p string) bool {
	return self.d.Has(p)
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
		self.d.Del(p)
	} else {
		m := MakeMset(tokens...)
		self.d.Set(p, m)
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
	if self.Has(p) {
		m := self.Get(p)
		m.Add(tokens)
	} else {
		self.d.Set(p, tokens.Copy())
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

func copykey (k interface{}) interface{} {
	return k
}

func copyval (v interface{}) interface{} {
	return v.(Mset).Copy()
}

func (self Marking) Copy () Marking {
	dict := self.d.Copy(copykey, copyval)
	return Marking{&dict, self.i}
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
	return (*(self.d.Fetch(p, MakeMset()))).(Mset)
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
	for _, key := range places {
		if self.Get(key).Empty() {
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
	for iter, p, m := other.Iter(); p != nil; p, m = iter.Next() {
		mine := self.Get(*p)
		if m.Geq(mine) {
			self.d.Del(*p)
		} else {
			mine.Sub(*m)
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
	iter *dicts.DictIterator
}

func (self MarkingIterator) Next () (*string, *Mset) {
	next := self.iter.Next()
	if next == nil {
		return nil, nil
	} else {
		p := (*next.Key).(string)
		m := (*next.Value).(Mset)
		return &p,  &m
	}
}

func (self Marking) Iter () (MarkingIterator, *string, *Mset) {
	iter, item := self.d.Iter()
	myiter := MarkingIterator{&iter}
	if item == nil {
		return myiter, nil, nil
	} else {
		p := (*item.Key).(string)
		m := (*item.Value).(Mset)
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
