// Python3 dicts ported to Go, inspired from a Python version at
// https://code.activestate.com/recipes/578375/

package dicts

import (
	"bytes"
	"fmt"
	"reflect"
)

//
// hash any value
//

const _FREE  int64 = -1
const _DUMMY int64 = -2

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

//
// compare any values
//

type equatable interface {
	Eq (interface{}) bool
}


func Eq (a, b interface{}) bool {
	i, ok := a.(equatable)
	if ok {
		return i.Eq(b)
	}
	return reflect.DeepEqual(a, b)
}

//
// dict type
//

type Item struct {
	Key   *interface{}
	Value *interface{}
	hash  uint64
}

type Dict struct {
	indices   map[uint64]int64
	itemlist  []Item
	used      uint64
	filled    uint64
	keyhash   uint64
}

func (self *Dict) Clear () {
	self.indices  = make(map[uint64]int64)
	self.itemlist = make([]Item, 0)
	self.used     = 0
	self.filled   = 0
	self.keyhash  = 0
}

type copyfunc func(interface{})interface{}

func (self Dict) Copy (copiers ...copyfunc) Dict {
	d := Dict{}
	d.indices = make(map[uint64]int64)
	for k, v := range self.indices {
		d.indices[k] = v
	}
	d.itemlist = make([]Item, len(self.itemlist))
	if len(copiers) == 0 {
		copy(d.itemlist, self.itemlist)
	} else if len(copiers) == 1 {
		cpk := copiers[0]
		for index, item := range self.itemlist {
			k := cpk(*(item.Key))
			d.itemlist[index] = Item{&k, item.Value, item.hash}
		}
	} else if len(copiers) == 2 {
		cpk := copiers[0]
		cpv := copiers[1]
		for index, item := range self.itemlist {
			k := cpk(*(item.Key))
			v := cpv(*(item.Value))
			d.itemlist[index] = Item{&k, &v, item.hash}
		}
	} else {
		panic("at most two copiers are allowed")
	}
	d.used = self.used
	d.filled = self.filled
	d.keyhash  = self.keyhash
	return d
}

func MakeDict (items ...Item) Dict {
	d := Dict{}
	d.Clear()
	for _, i := range items {
		d.Set(*(i.Key), *(i.Value))
	}
	return d
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

func (self Dict) lookup (key interface{}, hashvalue uint64) (int64, uint64) {
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

func (self Dict) Get (key interface{}) *interface{} {
	index, _ := self.lookup(key, Hash(key))
	if index < 0 {
		return nil
	}
	return self.itemlist[index].Value
}

func (self Dict) GetItem (key interface{}) *Item {
	index, _ := self.lookup(key, Hash(key))
	if index < 0 {
		return nil
	}
	return &self.itemlist[index]
}

func (self Dict) Fetch (key interface{}, fallback interface{}) *interface{} {
	index, _ := self.lookup(key, Hash(key))
	if index < 0 {
		return &fallback
	} else {
		return self.itemlist[index].Value
	}
}

func (self *Dict) Set (key interface{}, value interface{}) {
	hashvalue := Hash(key)
	index, i := self.lookup(key, hashvalue)
	if index < 0 {
		self.indices[i] = int64(self.used)
		self.itemlist = append(self.itemlist, Item{&key, &value, hashvalue})
		self.used++
		if index == _FREE {
			self.filled++
		}
		self.keyhash += hashvalue
	} else {
		self.itemlist[index] = Item{&key, &value, hashvalue}
	}
}

func (self *Dict) Del (key interface{}) {
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
			panic("inconsistent Dict internal state")
		}
		self.indices[j]       = index
		self.itemlist[index]  = lastitem
	}
	self.itemlist  = self.itemlist[:self.used]
	self.keyhash -= hashvalue
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

func (self Dict) Has (key interface{}) bool {
	index, _ := self.lookup(key, Hash(key))
	return index >= 0
}

func (self *Dict) Pop () Item {
	if self.used == 0 {
		panic("cannot Pop from empty Dict")
	}
	item := self.itemlist[self.used-1]
	self.Del(*(item.Key))
	self.keyhash -= item.hash
	return item
}

func (self Dict) Hash () uint64 {
	var h uint64 = 1959494633841095838 + self.keyhash
	for i := uint64(0); i < self.used; i++ {
		h += 5 * Hash(*(self.itemlist[i].Value)) + 1
	}
	return h
}

func (self Dict) Eq (other interface{}) bool {
	d, ok := other.(Dict)
	if ok {
		if self.Len() != d.Len() {
			return false
		} else if self.keyhash != d.keyhash {
			return false
		}
		for i := uint64(0); i < self.used; i++ {
			value := d.Get(*(self.itemlist[i].Key))
			if value == nil {
				return false
			} else if ! Eq(*(self.itemlist[i].Value), *(value)) {
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

func (self Dict) String () string {
	buf := bytes.NewBufferString("{")
	for i := uint64(0); i < self.used; i++ {
		if i > 0 {
			buf.WriteString(", ")
		}
		buf.WriteString(fmt.Sprintf("%#v", *(self.itemlist[i].Key)))
		buf.WriteString(": ")
		buf.WriteString(fmt.Sprintf("%#v", *(self.itemlist[i].Value)))
	}
	buf.WriteString("}")
	return buf.String()
}

func (self Item) String () string {
	return fmt.Sprintf("Item{%s}",
		fmt.Sprintf("%#v, %#v, %#v",
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
