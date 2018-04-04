package zn

import "fmt"
import "bytes"
import "dicts"

type Mset struct {
	d *dicts.Dict
}

func (self Mset) Hash () uint64 {
	return self.d.Hash()
}

func (self Mset) Eq (other interface{}) bool {
	m, ok := other.(Mset)
	if ok {
		return self.d.Eq(*(m.d))
	} else {
		return false
	}
}

//+++ zn.MakeMset(1, 2, 2, 3, 3, 3).Hash() == zn.MakeMset(3, 3, 3, 2, 2, 1).Hash()
//+++ zn.MakeMset(1, 2, 2, 3, 3, 3).Hash() == zn.MakeMset(3, 2, 1, 3, 2, 3).Hash()

func MakeMset (values ...interface{}) Mset {
	dict := dicts.MakeDict()
	mset := Mset{&dict}
	for _, elt := range values {
		count := (*mset.d.Fetch(elt, uint64(0))).(uint64)
		mset.d.Set(elt, count + 1)
	}
	return mset
}

//+++ zn.MakeMset().Eq(zn.MakeMset())
//--- zn.MakeMset().Eq(zn.MakeMset(1, 2, 3))
//--- zn.MakeMset().Eq(zn.MakeMset(1, 1, 1))
//+++ zn.MakeMset(1, 1, 1).Eq(zn.MakeMset(1, 1, 1))
//--- zn.MakeMset(1, 1, 3).Eq(zn.MakeMset(1, 1, 1))
//--- zn.MakeMset(1, 1, 1).Eq(zn.MakeMset(2, 2, 2))

func (self Mset) Copy () Mset {
	dict := self.d.Copy()
	return Mset{&dict}
}

//+++ zn.MakeMset(1, 2, 2, 3, 3, 3).Copy().Eq(zn.MakeMset(1, 2, 2, 3, 3, 3))

func (self Mset) Len () uint64 {
	count := uint64(0)
	for iter, item := self.d.Iter(); item != nil; item = iter.Next() {
		count += (*(item.Value)).(uint64)
	}
	return count
}

//+++ zn.MakeMset(1, 2, 2, 3, 3, 3).Len() == 6
//+++ zn.MakeMset().Len() == 0

func (self Mset) Add (other Mset) Mset {
	for iter, item := other.d.Iter(); item != nil; item = iter.Next() {
		count := (*(self.d.Fetch(*(item.Key), uint64(0)))).(uint64)
		self.d.Set(*(item.Key), count + (*(item.Value)).(uint64))
	}
	return self
}

//### a := zn.MakeMset(1, 2, 3)
//... b := zn.MakeMset(2, 3, 4)
//... a.Add(b)
//... a.Eq(zn.MakeMset(1, 2, 2, 3, 3, 4))
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

//### a := zn.MakeMset(1, 2, 3)
//... b := zn.MakeMset(2, 3, 4)
//... a.Sub(b)
//... a.Eq(zn.MakeMset(1))
//=== true

//### a := zn.MakeMset(1, 2, 2, 3, 3, 3)
//... b := zn.MakeMset(1, 2, 3)
//... a.Sub(b)
//... a.Eq(zn.MakeMset(2, 3, 3))
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

//+++ zn.MakeMset(1, 2, 3).Geq(zn.MakeMset(1, 2, 3))
//+++ zn.MakeMset(1, 2, 3).Geq(zn.MakeMset(1, 2))
//+++ zn.MakeMset(1, 2, 2, 3).Geq(zn.MakeMset(1, 2, 3))
//+++ zn.MakeMset(1, 2, 2, 3).Geq(zn.MakeMset())
//+++ zn.MakeMset().Geq(zn.MakeMset())
//--- zn.MakeMset(1, 2, 2, 3).Geq(zn.MakeMset(1, 2, 3, 4))
//--- zn.MakeMset(1, 2, 3).Geq(zn.MakeMset(1, 2, 2, 3))
//--- zn.MakeMset().Geq(zn.MakeMset(1))

func (self Mset) Empty () bool {
	return self.d.Len() == 0
}

//+++ zn.MakeMset().Empty()
//+++ zn.MakeMset().Empty()
//--- zn.MakeMset(1, 2).Empty()

func (self Mset) Count (value interface{}) uint64 {
	return (*(self.d.Fetch(value, uint64(0)))).(uint64)
}

//### zn.MakeMset(1, 2, 2, 3, 3, 3).Count(1)
//=== 1

//### zn.MakeMset(1, 2, 2, 3, 3, 3).Count(2)
//=== 2

//### zn.MakeMset(1, 2, 2, 3, 3, 3).Count(3)
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
	return self.current.Key
}

func (self Mset) Iter () (MsetIterator, *interface{}) {
	iter, item := self.d.Iter()
	myiter := MsetIterator{iter, false, 0, item}
	if item == nil {
		return myiter, nil
	} else {
		return myiter, item.Key
	}
}

func (self Mset) IterDup () (MsetIterator, *interface{}) {
	iter, item := self.d.Iter()
	myiter := MsetIterator{iter, true, (*(item.Value)).(uint64) - 1, item}
	return myiter, item.Key
}

//### a := zn.MakeMset(1, 2, 2, 3, 3, 3)
//... t := 0
//... for i, n := a.Iter(); n != nil; n = i.Next() { t += (*n).(int) }
//... t
//=== 6

//### a := zn.MakeMset(1, 2, 2, 3, 3, 3)
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

//### a := zn.MakeMset(1, 2, 3)
//... a
//>>> list(sorted((eval(out)))) == [1, 2, 3]

//### a := zn.MakeMset(1, 2, 2, 3, 3, 3)
//... a
//>>> list(sorted(eval(out))) == [1, 2, 2, 3, 3, 3]

type mapfunc func (interface{}, uint64) (interface{}, uint64)

func (self Mset) Map (f mapfunc) Mset {
	copy := MakeMset()
	for iter, item := self.d.Iter(); item != nil; item = iter.Next() {
		k := *(item.Key)
		v := (*(item.Value)).(uint64)
		k, v = f(k, v)
		copy.d.Set(k, v)
	}
	return copy
}

//### a := zn.MakeMset(1, 2, 2)
//... b := a.Map(func (v interface{}, n uint64) (interface{}, uint64) {return v.(int)+1, n})
//... b.Eq(zn.MakeMset(2, 3, 3))
//=== true

func (self Mset) ShowStructure () {
	self.d.ShowStructure()
}
