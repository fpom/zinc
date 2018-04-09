package zn

import "fmt"
import "bytes"

type Mset struct {
	h *Hashtable
	size uint64
}

func (self Mset) Hash () uint64 {
	return self.h.Hash()
}

func (self Mset) Eq (other interface{}) bool {
	m, ok := other.(Mset)
	if ok {
		if self.size != m.size {
			return false
		} else {
			return self.h == m.h || self.h.Eq(*(m.h))
		}
	} else {
		return false
	}
}

//+++ zn.MakeMset(1, 2, 2, 3, 3, 3).Hash() == zn.MakeMset(3, 3, 3, 2, 2, 1).Hash()
//+++ zn.MakeMset(1, 2, 2, 3, 3, 3).Hash() == zn.MakeMset(3, 2, 1, 3, 2, 3).Hash()

func MakeMset (values ...interface{}) Mset {
	ht := MakeHashtable(true)
	mset := Mset{&ht, uint64(len(values))}
	for _, elt := range values {
		k, v := ht.Get(elt)
		if k == nil {
			ht.Put(elt, uint64(1))
		} else {
			ht.Put(elt, (*v).(uint64) + 1)
		}
	}
	return mset
}

//+++ zn.MakeMset().Eq(zn.MakeMset())
//--- zn.MakeMset().Eq(zn.MakeMset(1, 2, 3))
//--- zn.MakeMset().Eq(zn.MakeMset(1, 1, 1))
//+++ zn.MakeMset(1, 1, 1).Eq(zn.MakeMset(1, 1, 1))
//--- zn.MakeMset(1, 1, 3).Eq(zn.MakeMset(1, 1, 1))
//--- zn.MakeMset(1, 1, 1).Eq(zn.MakeMset(2, 2, 2))

func (self Mset) Copy () interface{} {
	h := self.h.Copy()
	return Mset{&h, self.size}
}

//+++ zn.MakeMset(1, 2, 2, 3, 3, 3).Copy().Eq(zn.MakeMset(1, 2, 2, 3, 3, 3))

func (self Mset) Len () uint64 {
	return self.size
}

//+++ zn.MakeMset(1, 2, 2, 3, 3, 3).Len() == 6
//+++ zn.MakeMset().Len() == 0

func (self Mset) Add (other Mset) Mset {
	for iter, key, val := other.h.Iter(); key != nil; key, val = iter.Next() {
		k, v := self.h.Get(*key)
		if k == nil {
			self.h.Put(*key, (*val).(uint64))
		} else {
			self.h.Put(*key, (*v).(uint64) + (*val).(uint64))
		}
	}
	self.size += other.size
	return self
}

//### a := zn.MakeMset(1, 2, 3)
//... b := zn.MakeMset(2, 3, 4)
//... a.Add(b)
//... a.Eq(zn.MakeMset(1, 2, 2, 3, 3, 4))
//=== true

func (self Mset) Sub (other Mset) Mset {
	for iter, key, val := other.h.Iter(); key != nil; key, val = iter.Next() {
		k, v := self.h.Get(*key)
		if k != nil {
			left := (*v).(uint64)
			right := (*val).(uint64)
			if left <= right {
				self.h.Del(*key)
				self.size -= left
			} else {
				self.h.Put(*key, left - right)
				self.size -= right
			}
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
	if self.size < other.size {
		return false
	}
	for iter, key, val := other.h.Iter(); key != nil; key, val = iter.Next() {
		k, v := self.h.Get(*key)
		if k == nil {
			return false
		} else if (*v).(uint64) < (*val).(uint64) {
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
	return self.size == 0
}

//+++ zn.MakeMset().Empty()
//+++ zn.MakeMset().Empty()
//--- zn.MakeMset(1, 2).Empty()

func (self Mset) Count (value interface{}) uint64 {
	k, v := self.h.Get(value)
	if k == nil {
		return 0
	} else {
		return (*v).(uint64)
	}
}

//### zn.MakeMset(1, 2, 2, 3, 3, 3).Count(1)
//=== 1

//### zn.MakeMset(1, 2, 2, 3, 3, 3).Count(2)
//=== 2

//### zn.MakeMset(1, 2, 2, 3, 3, 3).Count(3)
//=== 3

type MsetIterator struct {
	iter    HashtableIterator
	dup     bool
	count   uint64
	key     *interface{}
}

func (self *MsetIterator) Next () *interface{} {
	var val *interface{}
	if self.key == nil {
		return nil
	} else if self.count == 0 {
		self.key, val = self.iter.Next()
		if self.key == nil {
			return nil
		} else if self.dup {
			self.count = (*(val)).(uint64) - 1
		}
	} else if self.dup {
		self.count--
	}
	return self.key
}

func (self Mset) Iter () (MsetIterator, *interface{}) {
	iter, key, _ := self.h.Iter()
	myiter := MsetIterator{iter, false, 0, key}
	if key == nil {
		return myiter, nil
	} else {
		return myiter, key
	}
}

func (self Mset) IterDup () (MsetIterator, *interface{}) {
	iter, key, val := self.h.Iter()
	myiter := MsetIterator{iter, true, 0, key}
	if key == nil {
		return myiter, nil
	} else {
		myiter.count = (*val).(uint64) - 1
		return myiter, key
	}
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
	for iter, key, val := self.h.Iter(); key != nil; key, val = iter.Next() {
		k := *key
		v := (*val).(uint64)
		k, v = f(k, v)
		copy.h.Put(k, v)
	}
	return copy
}
