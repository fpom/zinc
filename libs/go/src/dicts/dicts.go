// Go implementation Python3 dicts, translated from a Python version at
// https://code.activestate.com/recipes/578375/

package dicts

import (
	"strconv"
	"bytes"
	"fmt"
)

type Hashable interface {
	Hash () uint64
	Eq (other interface{}) bool
}

type Item struct {
	hash  int64
	Key   Hashable
	Value interface{}
}

type Dict struct {
	indices   map[int64]uint64
	itemlist  []Item
	used      uint64
	filled    uint64
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
		d.Set(i.Key, i.Value)
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

func (self Dict) Clear () {
	self.indices  = make(make[int64]int64)
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
	i         int64
	perturb   int64
}

func first_probe (hashvalue uint64) (int64, probe) {
	h := int64(hashvalue)
	if h < 0 {
		h = -h
	}
	p := probe{h, h}
	return p.i, p
}

func (self *probe) next () int64 {
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

func (self Dict) lookup (key Hashable, hashvalue uint64) (int64, int64) {
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
		} else if self.itemlist[index].hash == hashvalue && self.keylist[index].Eq(key) {
			return index, i
		}
	}
	// never reached
	return 0, 0
}

// def _resize(self, n):
//     '''Reindex the existing hash/key/value entries.
//        Entries do not get moved, they only get new indices.
//        No calls are made to hash() or __eq__().
//     '''
//     n = 2 ** n.bit_length()                     # round-up to power-of-two
//     self.indices = self._make_index(n)
//     for index, hashvalue in enumerate(self.hashlist):
//         for i in Dict._gen_probes(hashvalue, n-1):
//             if self.indices[i] == FREE:
//                 break
//         self.indices[i] = index
//     self.filled = self.used

func (self *Dict) resize (size uint64) {
	var n uint64 = 1 << uint64(len(strconv.FormatUint(size, 2)))
	self.indices = make([]uint64, n)
	for i := uint64(0); i < n; i++ {
		self.indices[i] = _FREE
	}
	for index, hashvalue := range self.hashlist {
		for i, p := first_probe(hashvalue, n-1); true; i = p.next() {
			if self.indices[i] == _FREE {
				break
			}
			self.indices[i] = uint64(index)
		}
	}
	self.filled = self.used
}

// def __getitem__(self, key):
//     hashvalue = hash(key)
//     index, i = self._lookup(key, hashvalue)
//     if index < 0:
//         raise KeyError(key)
//     return self.valuelist[index]

func (self Dict) Get (key Hashable) interface{} {
	index, _ := self.lookup(key, key.Hash())
	if index < _FIRST_HASH {
		panic("Dict has no such key")
	}
	return self.valuelist[index]
}

// def get(self, key, default=None):
//     index, i = self._lookup(key, hash(key))
//     return self.valuelist[index] if index >= 0 else default

func (self Dict) Fetch (key Hashable, fallback interface{}) interface{} {
	index, _ := self.lookup(key, key.Hash())
	if index < _FIRST_HASH {
		return fallback
	} else {
		return self.valuelist[index]
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
	hashvalue := key.Hash()
	index, i := self.lookup(key, hashvalue)
	if index < _FIRST_HASH {
		self.indices[i] = self.used
		self.hashlist   = append(self.hashlist, hashvalue)
		self.keylist    = append(self.keylist, key)
		self.valuelist  = append(self.valuelist, value)
		self.used++
		if index == _FREE {
			self.filled++
			if self.filled * 3 > uint64(len(self.indices)) * 2 {
				self.resize(4 * self.used)
			}
		}		
	} else {
		self.valuelist[index] = value
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
	hashvalue := key.Hash()
	index, i := self.lookup(key, hashvalue)
	if index < _FIRST_HASH {
		return
	}
	self.indices[i] = _DUMMY
	self.used--
	if index != self.used {
		lasthash     := self.hashlist[len(self.hashlist)-1]
		lastkey      := self.keylist[len(self.keylist)-1]
		lastvalue    := self.valuelist[len(self.valuelist)-1]
		lastindex, j := self.lookup(lastkey, lasthash)
		if lastindex < _FIRST_HASH || i == j {
			panic("inconsistent Dict internal state")
		}
		self.indices[j]       = index
		self.hashlist[index]  = lasthash
		self.keylist[index]   = lastkey
		self.valuelist[index] = lastvalue
	}
	self.hashlist  = self.hashlist[:len(self.hashlist)-1]
	self.keylist   = self.keylist[:len(self.keylist)-1]
	self.valuelist = self.valuelist[:len(self.valuelist)-1]
}

// def keys(self):
//     return list(self.keylist)

func (self Dict) Keys () []Hashable {
	var keys []Hashable
	copy(keys, self.keylist)
	return keys
}

// def values(self):
//     return list(self.valuelist)

func (self Dict) Values () []interface{} {
	var values []interface{}
	copy(values, self.valuelist)
	return values
}

// def items(self):
//     return zip(self.keylist, self.valuelist)

func (self Dict) Items () []Item {
	items := make([]Item, self.used)
	for i := uint64(0); i < self.used; i++ {
		items[i] = Item{self.keylist[i], self.valuelist[i]}
	}
	return items
}

// def __contains__(self, key):
//     index, i = self._lookup(key, hash(key))
//     return index >= 0

func (self Dict) Has (key Hashable) bool {
	index, _ := self.lookup(key, key.Hash())
	return index >= _FIRST_HASH
}

// def popitem(self):
//     if not self.keylist:
//         raise KeyError('popitem(): dictionary is empty')
//     key = self.keylist[-1]
//     value = self.valuelist[-1]
//     del self[key]
//     return key, value

func (self *Dict) Pop () (Hashable, interface{}) {
	if self.used == 0 {
		panic("cannot Pop from empty Dict")
	}
	key := self.keylist[len(self.keylist)-1]
	value := self.valuelist[len(self.valuelist)-1]
	self.Del(key)
	return key, value
}

func (self *Dict) PopItem () Item {
	key, value := self.Pop()
	return Item{key, value}
}

// def __repr__(self):
//     return 'Dict(%r)' % self.items()

func (self Dict) String () string {
	buf := bytes.NewBufferString("{")
	for i := uint64(0); i < self.used; i++ {
		if i > 0 && i < self.used-1 {
			buf.WriteString(", ")
		}
		buf.WriteString(fmt.Sprint(self.keylist[i]))
		buf.WriteString(": ")
		buf.WriteString(fmt.Sprint(self.valuelist[i]))
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

func (self Dict) ShowStructure () {
	for i:=0; i < 50; i++ {
		fmt.Print("=")
	}
	fmt.Println()
	fmt.Println(self)
	fmt.Println("Indices: ", self.indices)
	for i := uint64(0); i < self.used; i++ {
		fmt.Println(self.keylist[i], self.valuelist[i])
	}
	for i:=0; i < 50; i++ {
		fmt.Print("-")
	}
	fmt.Println()
}
