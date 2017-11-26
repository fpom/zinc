// Go implementation Python3 dicts, translated from a Python version at
// https://code.activestate.com/recipes/578375/

package dicts

import (
	"bytes"
	"fmt"
)

type Hashable interface {
	Hash () uint64
	Eq (other interface{}) bool
}

type Item struct {
	Key   *Hashable
	Value *interface{}
	hash  uint64
}

type Dict struct {
	indices   map[uint64]int64
	itemlist  []Item
	used      uint64
	filled    uint64
}

func hash (key Hashable) uint64 {
	h := int64(key.Hash())
	if h < 0 {
		return uint64(-h)
	} else {
		return uint64(h)
	}
}

// # Placeholder constants
// FREE = -1
// DUMMY = -2

const _FREE  int64 = -1
const _DUMMY int64 = -2

// def __init__(self, *args, **kwds):
//     if not hasattr(self, 'keylist'):
//         self.clear()
//     self.update(*args, **kwds)

func NewDict (items ...Item) Dict {
	d := Dict{}
	d.Clear()
	for _, i := range items {
		d.Set(*(i.Key), *(i.Value))
	}
	return d
}

// def _make_index(n):
//     'New sequence of indices using the smallest possible datatype'
//     # if n <= 2**7: return array.array('b', [FREE]) * n       # signed char
//     # if n <= 2**15: return array.array('h', [FREE]) * n      # signed short
//     # if n <= 2**31: return array.array('l', [FREE]) * n      # signed long
//     return [FREE] * n                                       # python integers
//
// def clear(self):
//     self.indices = self._make_index(8)
//     self.hashlist = []
//     self.keylist = []
//     self.valuelist = []
//     self.used = 0
//     self.filled = 0                                         # used + dummies

func (self *Dict) Clear () {
	self.indices  = make(map[uint64]int64)
	self.itemlist = make([]Item, 0)
	self.used     = 0
	self.filled   = 0
}

// def __len__(self):
//     return self.used

func (self Dict) Len () uint64 {
	return self.used
}

// def _gen_probes(hashvalue, mask):
//     'Same sequence of probes used in the current dictionary design'
//     PERTURB_SHIFT = 5
//     if hashvalue < 0:
//         hashvalue = -hashvalue
//     i = hashvalue & mask
//     yield i
//     perturb = hashvalue
//     while True:
//         i = (5 * i + perturb + 1) & 0xFFFFFFFFFFFFFFFF
//         yield i & mask
//         perturb >>= PERTURB_SHIFT

const _PERTURB_SHIFT uint64 = 5

type probe struct {
	i         uint64
	perturb   uint64
}

func first_probe (hashvalue uint64) (uint64, probe) {
	p := probe{hashvalue, hashvalue}
	return p.i, p
}

func (self *probe) next () uint64 {
	self.i = 5 * self.i + self.perturb + 1
	self.perturb >>= _PERTURB_SHIFT
	return self.i
}

// def _lookup(self, key, hashvalue):
//     'Same lookup logic as currently used in real dicts'
//     assert self.filled < len(self.indices)   # At least one open slot
//     freeslot = None
//     for i in self._gen_probes(hashvalue, len(self.indices)-1):
//         index = self.indices[i]
//         if index == FREE:
//             return (FREE, i) if freeslot is None else (DUMMY, freeslot)
//         elif index == DUMMY:
//             if freeslot is None:
//                 freeslot = i
//         elif (self.keylist[index] is key or
//               self.hashlist[index] == hashvalue
//               and self.keylist[index] == key):
//                 return (index, i)

func (self Dict) lookup (key Hashable, hashvalue uint64) (int64, uint64) {
	var freeslot *uint64 = nil
	for i, p := first_probe(hashvalue); true; i = p.next() {
		index, found := self.indices[i]
		if ! found {
			if freeslot == nil {
				return _FREE, i
			} else {
				return _DUMMY, *freeslot
			}
		} else if index == _DUMMY {
			if freeslot == nil {
				freeslot = new(uint64)
				*freeslot = i
			}
		} else if self.itemlist[index].Key == &key || (self.itemlist[index].hash == hashvalue && (*(self.itemlist[index].Key)).Eq(key)) {
			return index, i
		}
	}
	// never reached
	return 0, 0
}

// def __getitem__(self, key):
//     hashvalue = hash(key)
//     index, i = self._lookup(key, hashvalue)
//     if index < 0:
//         raise KeyError(key)
//     return self.valuelist[index]

func (self Dict) Get (key Hashable) interface{} {
	index, _ := self.lookup(key, hash(key))
	if index < 0 {
		panic("Dict has no such key")
	}
	return *(self.itemlist[index].Value)
}

// def get(self, key, default=None):
//     index, i = self._lookup(key, hash(key))
//     return self.valuelist[index] if index >= 0 else default

func (self Dict) Fetch (key Hashable, fallback interface{}) interface{} {
	index, _ := self.lookup(key, hash(key))
	if index < 0 {
		return fallback
	} else {
		return *(self.itemlist[index].Value)
	}
}

// def __setitem__(self, key, value):
//     hashvalue = hash(key)
//     index, i = self._lookup(key, hashvalue)
//     if index < 0:
//         self.indices[i] = self.used
//         self.hashlist.append(hashvalue)
//         self.keylist.append(key)
//         self.valuelist.append(value)
//         self.used += 1
//         if index == FREE:
//             self.filled += 1
//             if self.filled * 3 > len(self.indices) * 2:
//                 self._resize(4 * len(self))
//     else:
//         self.valuelist[index] = value

func (self *Dict) Set (key Hashable, value interface{}) {
	hashvalue := hash(key)
	index, i := self.lookup(key, hashvalue)
	if index < 0 {
		self.indices[i] = int64(self.used)
		self.itemlist = append(self.itemlist, Item{&key, &value, hashvalue})
		self.used++
		if index == _FREE {
			self.filled++
		}		
	} else {
		self.itemlist[index] = Item{&key, &value, hashvalue}
	}
}

// def __delitem__(self, key):
//     hashvalue = hash(key)
//     index, i = self._lookup(key, hashvalue)
//     if index < 0:
//         raise KeyError(key)
//     self.indices[i] = DUMMY
//     self.used -= 1
//     # If needed, swap with the lastmost entry to avoid leaving a "hole"
//     if index != self.used:
//         lasthash = self.hashlist[-1]
//         lastkey = self.keylist[-1]
//         lastvalue = self.valuelist[-1]
//         lastindex, j = self._lookup(lastkey, lasthash)
//         assert lastindex >= 0 and i != j
//         self.indices[j] = index
//         self.hashlist[index] = lasthash
//         self.keylist[index] = lastkey
//         self.valuelist[index] = lastvalue
//     # Remove the lastmost entry
//     self.hashlist.pop()
//     self.keylist.pop()
//     self.valuelist.pop()

func (self *Dict) Del (key Hashable) {
	hashvalue := hash(key)
	index, i := self.lookup(key, hashvalue)
	if index < 0 {
		return
	}
	self.indices[i] = _DUMMY
	self.used--
	if uint64(index) != self.used {
		lastitem     := self.itemlist[self.used]
		lastindex, j := self.lookup(*(lastitem.Key), lastitem.hash)
		if lastindex < 0 || i == j {
			panic("inconsistent Dict internal state")
		}
		self.indices[j]       = index
		self.itemlist[index]  = lastitem
	}
	self.itemlist  = self.itemlist[:self.used]
}

// def keys(self):
//     return list(self.keylist)
// def values(self):
//     return list(self.valuelist)
// def items(self):
//     return zip(self.keylist, self.valuelist)

type dictiter struct {
	i uint64
	d *Dict
}

func (self *dictiter) Next () *Item {
	self.i++
	if self.i >= self.d.used {
		return nil
	} else {
		return &(self.d.itemlist[self.i])
	}	
}

func (self Dict) Iter () (dictiter, *Item) {
	it := dictiter{0, &self}
	if self.used == 0 {
		return it, nil
	} else {
		return it, &(self.itemlist[0])
	}
}

// def __contains__(self, key):
//     index, i = self._lookup(key, hash(key))
//     return index >= 0

func (self Dict) Has (key Hashable) bool {
	index, _ := self.lookup(key, hash(key))
	return index >= 0
}

// def popitem(self):
//     if not self.keylist:
//         raise KeyError('popitem(): dictionary is empty')
//     key = self.keylist[-1]
//     value = self.valuelist[-1]
//     del self[key]
//     return key, value

func (self *Dict) Pop () Item {
	if self.used == 0 {
		panic("cannot Pop from empty Dict")
	}
	item := self.itemlist[self.used-1]
	self.Del(*(item.Key))
	return item
}

// def __repr__(self):
//     return 'Dict(%r)' % self.items()

func (self Dict) String () string {
	buf := bytes.NewBufferString("{")
	for i := uint64(0); i < self.used; i++ {
		if i > 0 {
			buf.WriteString(", ")
		}
		buf.WriteString(fmt.Sprint(*(self.itemlist[i].Key)))
		buf.WriteString(": ")
		buf.WriteString(fmt.Sprint(*(self.itemlist[i].Value)))
	}
	buf.WriteString("}")
	return buf.String()
}

// def show_structure(self):
//     'Diagnostic method.  Not part of the API.'
//     print '=' * 50
//     print self
//     print 'Indices:', self.indices
//     for i, row in enumerate(zip(self.hashlist, self.keylist, self.valuelist)):
//         print i, row
//     print '-' * 50

func (self Item) String () string {
	return fmt.Sprintf("Item{%s}",
		fmt.Sprintf("%s, %s, %d",
			fmt.Sprint(*(self.Key)),
			fmt.Sprint(*(self.Value)),
			self.hash))
}

func (self Dict) ShowStructure () {
	for i:=0; i < 50; i++ {
		fmt.Print("=")
	}
	fmt.Println()
	fmt.Println(self)
	fmt.Println("Indices: ", self.indices)
	for i := uint64(0); i < self.used; i++ {
		fmt.Println(self.itemlist[i])
	}
	for i:=0; i < 50; i++ {
		fmt.Print("-")
	}
	fmt.Println()
}
