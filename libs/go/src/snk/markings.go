package snk

import "fmt"
import "bytes"
import "hash/fnv"

type Marking struct {
	id int
	data *map[string]*Mset
}

func (self *Marking) SetId (id int) {
	self.id = id
}

func MakeMarking (id ...int) Marking {
	m := make(map[string]*Mset)
	if len(id) == 0 {
		return Marking{-1, &m}
	} else if len(id) == 1 {
		return Marking{id[0], &m}
	} else {
		panic("at most one id expected")
	}
}

func (self Marking) Hash () uint64 {
	var h uint64 = 2471033218594493899
	hash := fnv.New64()
	for place, tokens := range *self.data {
		hash.Reset()
		hash.Write([]byte(fmt.Sprintf("[%s]{%x}", place, tokens.Hash())))
		h ^= hash.Sum64()
	}
	return h
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
	if len(*self.data) != len(*other.data) {
		return false
	}
	for place, left := range *self.data {
		if right, found := (*other.data)[place] ; found {
			if ! left.Eq(*right) {
				return false
			}
		} else {
			return false
		}
	}
	return true
}

//+++ snk.MakeMarking().Eq(snk.MakeMarking())

func (self Marking) Set (place string, tokens ...interface{}) {
	if len(tokens) == 0 {
		delete(*self.data, place)
	} else {
		m := MakeMset(tokens...)
		(*self.data)[place] = &m
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

func (self Marking) Update (place string, tokens Mset) {
	if _, found := (*self.data)[place] ; found {
		(*self.data)[place].Add(tokens)
	} else {
		m := tokens.Copy()
		(*self.data)[place] = &m
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
	for key, value := range *self.data {
		m := value.Copy()
		(*copy.data)[key] = &m
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

func (self Marking) Get (place string) Mset {
	if value, found := (*self.data)[place] ; found {
		return *value
	} else {
		return MakeMset()
	}
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
		if value, found := (*self.data)[key] ; found {
			if value.Empty() {
				return false
			}
		} else {
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
	for place, right := range *other.data {
		self.Update(place, *right)
	}
	return self
}

//### a := snk.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... b := snk.MakeMarking()
//... b.Set("p2", 2, 4)
//... b.Set("p3", 1)
//... c := snk.MakeMarking()
//... c.Set("p1", 1, 2, 2, 3)
//... c.Set("p2", 1, 1, 2, 4, 4)
//... c.Set("p3", 1)
//... a.Add(b)
//... a.Eq(c)
//=== true

func (self Marking) Sub (other Marking) Marking {
	for place, right := range *other.data {
		if left, found := (*self.data)[place] ; found {
			left.Sub(*right)
			if left.Empty() {
				delete(*self.data, place)
			}
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
	for key, value := range *other.data {
		if mine, found := (*self.data)[key] ; found {
			if ! mine.Geq(*value) {
				return false
			}
		} else {
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

func (self Marking) Iter (place string) (MsetIterator, interface{}) {
	mset, found := (*self.data)[place]
	if found {
		return mset.Iter()
	} else {
		return MakeMset().Iter()
	}
}

func (self Marking) IterDup (place string) (MsetIterator, interface{}) {
	mset, found := (*self.data)[place]
	if found {
		return mset.IterDup()
	} else {
		return MakeMset().Iter()
	}
}

//### a := snk.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... fmt.Print("{")
//... for i, p := a.Iter("p1"); p != nil; p = i.Next() { fmt.Print(*p, ", ") }
//... fmt.Println("}")
//... nil
//>>> eval(out) == {1, 2, 3}

//### a := snk.MakeMarking()
//... a.Set("p1", 1, 2, 2, 3)
//... a.Set("p2", 1, 1, 4)
//... fmt.Print("{")
//... for i, p := a.Iter("p3"); p != nil; p = i.Next() { fmt.Print(*p, ", ") }
//... fmt.Println("}")
//... nil
//=== {}

func (self Marking) String () string {
	buf := bytes.NewBufferString("")
	if self.id >= 0 {
		buf.WriteString(fmt.Sprintf("[%d] ", self.id))
	}
	buf.WriteString("{")
	i := 0
	for key, value := range *self.data {
		if i > 0 {
			buf.WriteString(", ")
		}
		i += 1
		buf.WriteString(fmt.Sprintf(`"%s": %s`, key, value))
	}	
	buf.WriteString("}")
	return buf.String()
}
