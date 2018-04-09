// Python3 dicts ported to Go, inspired from a Python version at
// https://code.activestate.com/recipes/578375/

package zn

import (
	"reflect"
	"bytes"
	"fmt"
	"math/bits"
)

//
// generic hash / compare
//

type Hashable interface {
	Hash () uint64
}

func Hash (value interface{}) uint64 {
	h, err := doHash(value, nil)
	if err != nil {
		panic(err)
	}
	i := int64(h)
	if i < 0 {
		return uint64(-i)
	} else {
		return uint64(i)
	}
}

type Equatable interface {
	Eq (interface{}) bool
}

func Eq (a, b interface{}) bool {
	i, ok := a.(Equatable)
	if ok {
		return i.Eq(b)
	}
	return reflect.DeepEqual(a, b)
}

type Copyable interface {
	Copy() interface{}
}

func Copy (a interface{}) interface{} {
	i, ok := a.(Copyable)
	if ok {
		return i.Copy()
	} else {
		return a
	}
}

//
// items
//

type _Slot struct {
	hash uint64
	key  interface{}
}

//
// hashtables
//

type Hashtable struct {
	indices   []int64
	slots     []_Slot
	payloads  []interface{}
	haspl     bool
	used      uint64
	filled    uint64
	keyhash   uint64
}

const _FREE  int64 = -1
const _DUMMY int64 = -2

func MakeHashtable (payloads bool) Hashtable {
	return Hashtable{
		[]int64{_FREE, _FREE, _FREE, _FREE, _FREE, _FREE, _FREE, _FREE},
		make([]_Slot, 0),
		make([]interface{}, 0),
		payloads,
		0,
		0,
		0}
}

func (self *Hashtable) Clear () {
	*self = MakeHashtable(self.haspl)
}

func (self Hashtable) Copy () Hashtable {
	ht := Hashtable{
		make([]int64, len(self.indices)),
		make([]_Slot, len(self.slots)),
		make([]interface{}, len(self.payloads)),
		self.haspl,
		self.used,
		self.filled,
		self.keyhash}
	copy(ht.indices, self.indices)
	if self.haspl {
		for i := uint64(0); i < self.used; i++ {
			slot := &(self.slots[i])
			ht.slots[i] = _Slot{slot.hash, Copy(slot.key)}
			ht.payloads[i] = Copy(self.payloads[i])
		}
	} else {
		for i := uint64(0); i < self.used; i++ {
			slot := &(self.slots[i])
			ht.slots[i] = _Slot{slot.hash, Copy(slot.key)}
		}
	}
	return ht
}

func (self Hashtable) Len () uint64 {
	return self.used
}

type hGen struct {
	hash      uint64
	index     uint64
	perturb   uint64
	mask      uint64
}

func (self Hashtable) probe (hashvalue uint64) (uint64, hGen) {
	m := uint64(len(self.indices)) - 1
	g := hGen{hashvalue & m, hashvalue, hashvalue, m}
	return g.hash, g
}

const _PERTURB_SHIFT uint64 = 5

func (self *hGen) next () uint64 {
	self.index = 5 * self.index + self.perturb + 1
	self.hash = self.index & self.mask
	self.perturb >>= _PERTURB_SHIFT
	return self.hash
}

func (self Hashtable) lookup (key interface{}, hashvalue uint64) (int64, uint64) {
	var freeslot uint64
	var fsempty bool = true
	if self.filled >= uint64(len(self.indices)) {
		panic("no open slot")
	}
	for i, g := self.probe(hashvalue); true; i = g.next() {
		index := self.indices[i]
		switch index {
		case _FREE :
			if fsempty {
				return _FREE, i
			} else {
				return _DUMMY, freeslot
			}
		case _DUMMY :
			if fsempty {
				fsempty = false
				freeslot = i
			}
		default :
			if Eq(self.slots[index].key, key) {
				return index, i
			}
		}
	}
	panic("unreachable code has been reached")
}

func (self Hashtable) Get (key interface{}) (*interface{}, *interface{}) {
	index, _ := self.lookup(key, Hash(key))
	if index < 0 {
		return nil, nil
	} else if self.haspl {
		return &(self.slots[index].key), &(self.payloads[index])
	} else {
		return &(self.slots[index].key), nil
	}
}

func (self *Hashtable) resize (size uint64) {
	s := uint64(1) << uint64(bits.Len64(size))
	self.indices = make([]int64, s)
	for i := uint64(0); i < s; i++ {
		self.indices[i] = _FREE
	}
	for n := uint64(0); n < self.used; n++ {
		for i, p := self.probe(self.slots[n].hash); true; i = p.next() {
			if self.indices[i] == _FREE {
				self.indices[i] = int64(n)
				break
			}
		}
	}
	self.filled = self.used
}

func (self *Hashtable) Put (keyval ...interface{}) {
	if self.haspl {
		if len(keyval) != 2 {
			panic("two items expected (key and payload)")
		}
	} else if len(keyval) != 1 {
		panic("one item expected (key)")
	}
	key := keyval[0]
	hashvalue := Hash(key)
	index, i := self.lookup(key, hashvalue)
	if index < 0 {
		self.indices[i] = int64(self.used)
		self.slots = append(self.slots, _Slot{hashvalue, key})
		if self.haspl {
			self.payloads = append(self.payloads, keyval[1])
		}
		self.used++
		if index == _FREE {
			self.filled++
			if self.filled * 3 > uint64(len(self.indices)) * 2 {
				self.resize(4 * self.used)
			}
		}
		self.keyhash += hashvalue
	} else {
		self.slots[index] = _Slot{hashvalue, key}
		if self.haspl {
			self.payloads[index] = keyval[1]
		}
	}
}

func (self *Hashtable) Del (key interface{}) {
	hashvalue := Hash(key)
	index, i := self.lookup(key, hashvalue)
	if index < 0 {
		return
	}
	self.indices[i] = _DUMMY
	self.used--
	if uint64(index) != self.used {
		lastslot := &self.slots[self.used]
		lastindex, j := self.lookup(lastslot.key, lastslot.hash)
		if lastindex < 0 || i == j {
			panic("inconsistent Hashtable internal state")
		}
		self.indices[j] = index
		self.slots[index] = *lastslot
		if self.haspl{
			self.payloads[index] = self.payloads[self.used]
		}
	}
	self.slots = self.slots[:self.used]
	if self.haspl {
		self.payloads = self.payloads[:self.used]
	}
	self.keyhash -= hashvalue
}

type HashtableIterator struct {
	i uint64
	h *Hashtable
}

func (self *HashtableIterator) Next () (*interface{}, *interface{}) {
	self.i++
	if self.i >= self.h.used {
		return nil, nil
	} else if self.h.haspl {
		return &(self.h.slots[self.i].key), &(self.h.payloads[self.i])
	} else {
		return &(self.h.slots[self.i].key), nil
	}
}

func (self Hashtable) Iter () (HashtableIterator, *interface{}, *interface{}) {
	it := HashtableIterator{0, &self}
	if self.used == 0 {
		return it, nil, nil
	} else if self.haspl {
		return it, &(self.slots[0].key), &(self.payloads[0])
	} else {
		return it, &(self.slots[0].key), nil
	}
}

func (self Hashtable) Has (key interface{}) bool {
	index, _ := self.lookup(key, Hash(key))
	return index >= 0
}

func (self *Hashtable) Pop () (*interface{}, *interface{}) {
	var payload *interface{}
	var slot *_Slot
	if self.used == 0 {
		return nil, nil
	} else if self.haspl {
		slot = &(self.slots[self.used-1])
		payload = &(self.payloads[self.used-1])
	} else {
		slot = &(self.slots[self.used-1])
		payload = nil
	}
	self.Del(slot.key)
	self.keyhash -= slot.hash
	return &(slot.key), payload
}

func (self Hashtable) Hash () uint64 {
	if self.haspl {
		h := self.keyhash
		for i := uint64(0); i < self.used; i++ {
			h += 5 * Hash(self.payloads[i])
		}
		return h
	} else {
		return self.keyhash
	}
}

func (self Hashtable) Eq (other interface{}) bool {
	ht, ok := other.(Hashtable)
	if ok {
		if self.used != ht.used {
			return false
		} else if self.keyhash != ht.keyhash {
			return false
		} else if &self.slots == &ht.slots {
			return true
		}
		for i := uint64(0); i < self.used; i++ {
			if self.haspl {
				if &self.slots[i] == &ht.slots[i] && &self.payloads[i] != &ht.payloads[i] {
					return true
				}
			} else {
				if &self.slots[i] == &ht.slots[i] {
					return true
				}
			}
			key, val := ht.Get(self.slots[i].key)
			if key == nil {
				return false
			} else if self.haspl && ! Eq(self.payloads[i], *val) {
				return false
			}
		}
		return true
	} else {
		return false
	}
}

//
//
//

func (self Hashtable) String () string {
	buf := bytes.NewBufferString("{")
	for i := uint64(0); i < self.used; i++ {
		if i > 0 {
			buf.WriteString(", ")
		}
		if self.haspl {
			buf.WriteString(fmt.Sprintf("%#v: %s", self.slots[i].key, self.payloads[i]))
		} else {
			buf.WriteString(fmt.Sprintf("%#v", self.slots[i].key))
		}
	}
	buf.WriteString("}")
	return buf.String()
}
