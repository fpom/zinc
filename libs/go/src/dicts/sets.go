// Python3 dicts ported to Go, inspired from a Python version at
// https://code.activestate.com/recipes/578375/

package dicts

import (
	"bytes"
	"fmt"
	"math/bits"
)

//
// set type
//

type SetItem struct {
	Key   *interface{}
	hash  uint64
}

type Set struct {
	indices   []int64
	itemlist  []SetItem
	used      uint64
	filled    uint64
	keyhash   uint64
}

func (self *Set) Clear () {
	self.indices  = []int64{_FREE, _FREE, _FREE, _FREE, _FREE, _FREE, _FREE, _FREE}
	self.itemlist = make([]SetItem, 0)
	self.used     = 0
	self.filled   = 0
	self.keyhash  = 0
}

func (self Set) Copy (copiers ...copyfunc) Set {
	s := Set{
		make([]int64, len(self.indices)),
		make([]SetItem, len(self.itemlist)),
		self.used,
		self.filled,
		self.keyhash}
	copy(s.indices, self.indices)
	if len(copiers) == 0 {
		copy(s.itemlist, self.itemlist)
	} else if len(copiers) == 1 {
		cpk := copiers[0]
		for index, item := range self.itemlist {
			k := cpk(*(item.Key))
			s.itemlist[index] = SetItem{&k, item.hash}
		}
	} else {
		panic("at most one copier is allowed")
	}
	return s
}

func MakeSet (items ...interface{}) Set {
	s := Set{}
	s.Clear()
	for _, i := range items {
		s.Add(i)
	}
	return s
}

func (self Set) Len () uint64 {
	return self.used
}

type sprobe struct {
	i         uint64
	perturb   uint64
}

func (self Set) first_probe (hashvalue uint64) (uint64, probe) {
	m := uint64(len(self.indices)) - 1
	p := probe{hashvalue & m, hashvalue, hashvalue, m}
	return p.i, p
}

func (self Set) lookup (key interface{}, hashvalue uint64) (int64, uint64) {
	var freeslot uint64
	var fsempty bool = true
	if self.filled >= uint64(len(self.indices)) {
		panic("no open slot")
	}
	i, p := self.first_probe(hashvalue)
	for ; true; i = p.next() {
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
			item := self.itemlist[index]
			if item.Key == &key || item.hash == hashvalue && Eq(*(item.Key), key) {
				return index, i
			}
		}
	}
	panic("unreachable code has been reached")
}

func (self Set) Get (key interface{}) *interface{} {
	index, _ := self.lookup(key, Hash(key))
	if index < 0 {
		return nil
	}
	return self.itemlist[index].Key
}

func (self Set) Fetch (key interface{}, fallback interface{}) *interface{} {
	index, _ := self.lookup(key, Hash(key))
	if index < 0 {
		return &fallback
	} else {
		return self.itemlist[index].Key
	}
}

func (self *Set) resize (size uint64) {
	s := uint64(1) << uint64(bits.Len64(size))
	self.indices = make([]int64, s)
	for i := uint64(0); i < s; i++ {
		self.indices[i] = _FREE
	}
	for index, item := range self.itemlist {
		for i, p := self.first_probe(item.hash); true; i = p.next() {
			if self.indices[i] == _FREE {
				self.indices[i] = int64(index)
				break
			}
		}
	}
	self.filled = self.used
}

func (self *Set) Add (key interface{}) {
	hashvalue := Hash(key)
	index, i := self.lookup(key, hashvalue)
	if index < 0 {
		self.indices[i] = int64(self.used)
		self.itemlist = append(self.itemlist, SetItem{&key, hashvalue})
		self.used++
		if index == _FREE {
			self.filled++
			if self.filled * 3 > uint64(len(self.indices)) * 2 {
				self.resize(4 * self.used)
			}
		}
		self.keyhash += hashvalue
	} else {
		self.itemlist[index] = SetItem{&key, hashvalue}
	}
}

func (self *Set) Del (key interface{}) {
	hashvalue := Hash(key)
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
			panic("inconsistent Set internal state")
		}
		self.indices[j]       = index
		self.itemlist[index]  = lastitem
	}
	self.keyhash -= hashvalue
}

type SetIterator struct {
	i uint64
	s *Set
}

func (self *SetIterator) Next () *SetItem {
	self.i++
	if self.i >= self.s.used {
		return nil
	} else {
		return &(self.s.itemlist[self.i])
	}
}

func (self Set) Iter () (SetIterator, *SetItem) {
	it := SetIterator{0, &self}
	if self.used == 0 {
		return it, nil
	} else {
		return it, &(self.itemlist[0])
	}
}

func (self Set) Has (key interface{}) bool {
	index, _ := self.lookup(key, Hash(key))
	return index >= 0
}

func (self *Set) Pop () SetItem {
	if self.used == 0 {
		panic("cannot Pop from empty Set")
	}
	item := self.itemlist[self.used-1]
	self.Del(*(item.Key))
	self.keyhash -= item.hash
	return item
}

func (self Set) Hash () uint64 {
	return self.keyhash
}

func (self Set) Eq (other interface{}) bool {
	s, ok := other.(Set)
	if ok {
		if self.Len() != s.Len() {
			return false
		} else if self.keyhash != s.keyhash {
			return false
		}
		for i := uint64(0); i < self.used; i++ {
			value := s.Get(*(self.itemlist[i].Key))
			if value == nil {
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

func (self Set) String () string {
	buf := bytes.NewBufferString("{")
	for i := uint64(0); i < self.used; i++ {
		if i > 0 {
			buf.WriteString(", ")
		}
		buf.WriteString(fmt.Sprintf("%#v", *(self.itemlist[i].Key)))
	}
	buf.WriteString("}")
	return buf.String()
}

func (self SetItem) String () string {
	return fmt.Sprintf("SetItem{%s}",
		fmt.Sprintf("%#v, %#v",
			fmt.Sprint(*(self.Key)),
			self.hash))
}

func (self Set) ShowStructure () {
	for i:=0; i < 50; i++ {
		fmt.Print("=")
	}
	fmt.Println()
	fmt.Println(self)
	fmt.Println("Indices:", self.indices)
	fmt.Println("Items:")
	for i := uint64(0); i < self.used; i++ {
		fmt.Printf(" [%d] %s\n", i, self.itemlist[i])
	}
	for i:=0; i < 50; i++ {
		fmt.Print("-")
	}
	fmt.Println()
}
