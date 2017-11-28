package snk

import "fmt"
import "bytes"
import "hash/fnv"
import "hashstructure"
import "dicts"

type Mset struct {
	d *dicts.Dict
}

func (self Mset) Hash () uint64 {
	var h uint64 = 13124430844775843711
	hash := fnv.New64()
	for iter, item := self.d.Iter(); item != nil; item = iter.Next() {
		hv, err := hashstructure.Hash(*(item.Key), nil)
		if err != nil {
			panic(err)
		}
		hash.Reset()
		hash.Write([]byte(fmt.Sprintf("[%x]{%x}", hv, *(item.Value))))
		h ^= hash.Sum64()
	}
	return h
}

type AsString struct {
	val *interface{}
}

func (self AsString) Hash () uint64 {
	return dicts.StringHash(fmt.Sprint(*(self.val)))
}

func (self AsString) Eq (other interface{}) bool {
	if v, ok := other.(AsString); ok {
		return fmt.Sprint(*(self.val)) == fmt.Sprint(*(v.val))
	} else {
		return fmt.Sprint(*(self.val)) == fmt.Sprint(other)
	}
}

func i2h (v interface{}) dicts.Hashable {
	return AsString{&v}
}

func h2i (v *dicts.Hashable) *interface{} {
	return (*v).(AsString).val
}

//+++ snk.MakeMset(1, 2, 2, 3, 3, 3).Hash() == snk.MakeMset(3, 3, 3, 2, 2, 1).Hash()
//+++ snk.MakeMset(1, 2, 2, 3, 3, 3).Hash() == snk.MakeMset(3, 2, 1, 3, 2, 3).Hash()

func MakeMset (values ...interface{}) Mset {
	dict := dicts.MakeDict()
	mset := Mset{&dict}
	for _, elt := range values {
		h := i2h(elt)
		count := (*mset.d.Fetch(h, uint64(0))).(uint64)
		mset.d.Set(h, count + 1)
	}
	return mset
}

func (self Mset) Eq (other Mset) bool {
	if self.d.Len() != other.d.Len() {
		return false
	}
	for iter, item := self.d.Iter(); item != nil; item = iter.Next() {
		if ! other.d.Has(*(item.Key)) {
			return false
		} else if (*item.Value).(uint64) != (*other.d.Get(*(item.Key))).(uint64) {
			return false
		}
	}
	return true
}

//+++ snk.MakeMset().Eq(snk.MakeMset())
//--- snk.MakeMset().Eq(snk.MakeMset(1, 2, 3))
//--- snk.MakeMset().Eq(snk.MakeMset(1, 1, 1))
//+++ snk.MakeMset(1, 1, 1).Eq(snk.MakeMset(1, 1, 1))
//--- snk.MakeMset(1, 1, 3).Eq(snk.MakeMset(1, 1, 1))
//--- snk.MakeMset(1, 1, 1).Eq(snk.MakeMset(2, 2, 2))

func (self Mset) Copy () Mset {
	copy := MakeMset()
	for iter, item := self.d.Iter(); item != nil; item = iter.Next() {
		copy.d.Set(*(item.Key), *(item.Value))
	}
	return copy
}

//+++ snk.MakeMset(1, 2, 2, 3, 3, 3).Copy().Eq(snk.MakeMset(1, 2, 2, 3, 3, 3))

func (self Mset) Len () uint64 {
	count := uint64(0)
	for iter, item := self.d.Iter(); item != nil; item = iter.Next() {
		count += (*(item.Value)).(uint64)
	}
	return count
}

//+++ snk.MakeMset(1, 2, 2, 3, 3, 3).Len() == 6
//+++ snk.MakeMset().Len() == 0

func (self Mset) Add (other Mset) Mset {
	for iter, item := other.d.Iter(); item != nil; item = iter.Next() {
		count := (*(self.d.Fetch(*(item.Key), uint64(0)))).(uint64)
		self.d.Set(*(item.Key), count + (*(item.Value)).(uint64))
	}
	return self
}

//### a := snk.MakeMset(1, 2, 3)
//... b := snk.MakeMset(2, 3, 4)
//... a.Add(b)
//... a.Eq(snk.MakeMset(1, 2, 2, 3, 3, 4))
//=== true

func (self Mset) Sub (other Mset) Mset {
	for iter, item := other.d.Iter(); item != nil; item = iter.Next() {
		left := (*(self.d.Fetch(*(item.Key), uint64(0)))).(uint64)
		right := (*(item.Value)).(uint64)
		if left <= right {
			self.d.Del(*(item.Key))
		} else {
			self.d.Set(*(item.Key), left - right)
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
	for iter, item := other.d.Iter(); item != nil; item = iter.Next() {
		count := (*(self.d.Fetch(*(item.Key), uint64(0)))).(uint64)
		if count < (*item.Value).(uint64) {
			return false
		}
	}
	return true
}

//+++ snk.MakeMset(1, 2, 3).Geq(snk.MakeMset(1, 2, 3))
//+++ snk.MakeMset(1, 2, 3).Geq(snk.MakeMset(1, 2))
//+++ snk.MakeMset(1, 2, 2, 3).Geq(snk.MakeMset(1, 2, 3))
//+++ snk.MakeMset(1, 2, 2, 3).Geq(snk.MakeMset())
//+++ snk.MakeMset().Geq(snk.MakeMset())
//--- snk.MakeMset(1, 2, 2, 3).Geq(snk.MakeMset(1, 2, 3, 4))
//--- snk.MakeMset(1, 2, 3).Geq(snk.MakeMset(1, 2, 2, 3))
//--- snk.MakeMset().Geq(snk.MakeMset(1))

func (self Mset) Empty () bool {
	return self.d.Len() == 0
}

//+++ snk.MakeMset().Empty()
//+++ snk.MakeMset().Empty()
//--- snk.MakeMset(1, 2).Empty()

func (self Mset) Count (value interface{}) uint64 {
	return (*(self.d.Fetch(i2h(value), uint64(0)))).(uint64)
}

//### snk.MakeMset(1, 2, 2, 3, 3, 3).Count(1)
//=== 1

//### snk.MakeMset(1, 2, 2, 3, 3, 3).Count(2)
//=== 2

//### snk.MakeMset(1, 2, 2, 3, 3, 3).Count(3)
//=== 3

type MsetIterator struct {
	iter    dicts.DictIterator
	dup     bool
	count   uint64
	current *dicts.Item
}

func (self *MsetIterator) Next () *interface{} {
	if self.current == nil {
		return nil
	} else if self.count == 0 {
		self.current = self.iter.Next()
		if self.current == nil {
			return nil
		} else if self.dup {
			self.count = (*(self.current.Value)).(uint64) - 1
		}
	} else if self.dup {
		self.count--
	}
	return h2i(self.current.Key)
}

func (self Mset) Iter () (MsetIterator, *interface{}) {
	iter, item := self.d.Iter()
	myiter := MsetIterator{iter, false, 0, item}
	if item == nil {
		return myiter, nil
	} else {
		return myiter, h2i(item.Key)
	}
}

func (self Mset) IterDup () (MsetIterator, *interface{}) {
	iter, item := self.d.Iter()
	myiter := MsetIterator{iter, true, (*(item.Value)).(uint64) - 1, item}
	return myiter, h2i(item.Key)
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

func (self Mset) String () string {
	buf := bytes.NewBufferString("[")
	comma := false
	for iter, val := self.IterDup(); val != nil; val = iter.Next() {
		if comma {
			buf.WriteString(", ")
		} else {
			comma = true
		}
		buf.WriteString(fmt.Sprint(*val))
	}	
	buf.WriteString("]")
	return buf.String()
}

//### a := snk.MakeMset(1, 2, 3)
//... a
//>>> list(sorted((eval(out)))) == [1, 2, 3]

//### a := snk.MakeMset(1, 2, 2, 3, 3, 3)
//... a
//>>> list(sorted(eval(out))) == [1, 2, 2, 3, 3, 3]

type mapfunc func (interface{}, uint64) (interface{}, uint64)

func (self Mset) Map (f mapfunc) Mset {
	copy := MakeMset()
	for iter, item := self.d.Iter(); item != nil; item = iter.Next() {
		k := *h2i(item.Key)
		v := (*(item.Value)).(uint64)
		k, v = f(k, v)
		copy.d.Set(i2h(k), v)
	}
	return copy
}

//### a := snk.MakeMset(1, 2, 2)
//... b := a.Map(func (v interface{}, n uint64) (interface{}, uint64) {return v.(int)+1, n})
//... b.Eq(snk.MakeMset(2, 3, 3))
//=== true

func (self Mset) ShowStructure () {
	self.d.ShowStructure()
}
