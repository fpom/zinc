// Python3 dicts ported to Go, inspired from a Python version at
// https://code.activestate.com/recipes/578375/

package dicts

import (
	"bytes"
	"fmt"
	"hash/fnv"
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

func StringHash (s string) uint64 {
	hash := fnv.New64()
	hash.Write([]byte(s))
	return hash.Sum64()
}

const _FREE  int64 = -1
const _DUMMY int64 = -2

func MakeDict (items ...Item) Dict {
	d := Dict{}
	d.Clear()
	for _, i := range items {
		d.Set(*(i.Key), *(i.Value))
	}
	return d
}

func (self *Dict) Clear () {
	self.indices  = make(map[uint64]int64)
	self.itemlist = make([]Item, 0)
	self.used     = 0
	self.filled   = 0
}

func (self Dict) Len () uint64 {
	return self.used
}

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
		} else {
			item := self.itemlist[index]
			if item.Key == &key || item.hash == hashvalue && (*item.Key).Eq(key) {
				return index, i
			}
		}
	}
	// never reached
	return 0, 0
}

func (self Dict) Get (key Hashable) *interface{} {
	index, _ := self.lookup(key, hash(key))
	if index < 0 {
		return nil
	}
	return self.itemlist[index].Value
}

func (self Dict) Fetch (key Hashable, fallback interface{}) *interface{} {
	index, _ := self.lookup(key, hash(key))
	if index < 0 {
		return &fallback
	} else {
		return self.itemlist[index].Value
	}
}

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

func (self *Dict) Del (key Hashable) {
	index, i := self.lookup(key, hash(key))
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

type DictIterator struct {
	i uint64
	d *Dict
}

func (self *DictIterator) Next () *Item {
	self.i++
	if self.i >= self.d.used {
		return nil
	} else {
		return &(self.d.itemlist[self.i])
	}	
}

func (self Dict) Iter () (DictIterator, *Item) {
	it := DictIterator{0, &self}
	if self.used == 0 {
		return it, nil
	} else {
		return it, &(self.itemlist[0])
	}
}

func (self Dict) Has (key Hashable) bool {
	index, _ := self.lookup(key, hash(key))
	return index >= 0
}

func (self *Dict) Pop () Item {
	if self.used == 0 {
		panic("cannot Pop from empty Dict")
	}
	item := self.itemlist[self.used-1]
	self.Del(*(item.Key))
	return item
}

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
