// Python3 dicts ported to Go, inspired from a Python version at
// https://code.activestate.com/recipes/578375/

package dicts

import (
	"bytes"
	"fmt"
)

//
// set type
//

type SetItem struct {
	Key   *interface{}
	hash  uint64
}

type Set struct {
	indices   map[uint64]int64
	itemlist  []SetItem
	used      uint64
	filled    uint64
	keyhash   uint64
}

func (self *Set) Clear () {
	self.indices  = make(map[uint64]int64)
	self.itemlist = make([]SetItem, 0)
	self.used     = 0
	self.filled   = 0
	self.keyhash  = 0
}

func (self Set) Copy (copiers ...copyfunc) Set {
	s := Set{}
	s.indices = make(map[uint64]int64)
	for k, v := range self.indices {
		s.indices[k] = v
	}
	s.itemlist = make([]SetItem, len(self.itemlist))
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
	s.used = self.used
	s.filled = self.filled
	s.keyhash  = self.keyhash
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

func (self Set) lookup (key interface{}, hashvalue uint64) (int64, uint64) {
	var freeslot uint64
	var fsempty bool = true
	for i, p := first_probe(hashvalue); true; i = p.next() {
		index, found := self.indices[i]
		if ! found {
			if fsempty {
				return _FREE, i
			} else {
				return _DUMMY, freeslot
			}
		} else if index == _DUMMY {
			if fsempty {
				fsempty = false
				freeslot = i
			}
		} else {
			item := self.itemlist[index]
			if item.Key == &key || item.hash == hashvalue && Eq(*(item.Key), key) {
				return index, i
			}
		}
	}
	// never reached
	panic("unreachable code has been reached")
	return 0, 0
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

func (self *Set) Add (key interface{}) {
	hashvalue := Hash(key)
	index, i := self.lookup(key, hashvalue)
	if index < 0 {
		self.indices[i] = int64(self.used)
		self.itemlist = append(self.itemlist, SetItem{&key, hashvalue})
		self.used++
		if index == _FREE {
			self.filled++
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
	self.itemlist  = self.itemlist[:self.used]
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
