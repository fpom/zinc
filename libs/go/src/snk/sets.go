package snk

type Set struct {
	data map[uint64]*Marking
}

//*** a := snk.MakeMarking()
//*** a.Set("p1", 1)
//*** b := a.Copy()
//*** b.Set("p2", 2)
//*** c := b.Copy()
//*** c.Set("p3", 3)

func MakeSet (markings ...*Marking) Set {
	set := Set{make(map[uint64]*Marking)}
	for _, m := range markings {
		set.AddPtr(m)
	}
	return set
}

func (self Set) Empty () bool {
	return len(self.data) == 0
}

func (self Set) NotEmpty () bool {
	return len(self.data) > 0
}

//+++ snk.MakeSet().Empty()
//--- snk.MakeSet(&a).Empty()
//--- snk.MakeSet().NotEmpty()
//+++ snk.MakeSet(&a).NotEmpty()

func (self Set) Len () int {
	return len(self.data)
}

//+++ snk.MakeSet().Len() == 0
//+++ snk.MakeSet(&a).Len() == 1
//+++ snk.MakeSet(&a, &a).Len() == 1

func (self Set) lookup (m *Marking) (uint64, bool) {
	slot := m.Hash()
	perturb := slot
	for true {
		if value, found := self.data[slot]; !found {
			return slot, false
		} else if value.Eq(*m) {
			return slot, true
		} else {
			slot = (5 * slot) + 1 + perturb
			perturb >>= 5
		}
	}
	return 0, false
}

func (self *Set) Add (m Marking) {
	self.AddPtr(&m)
}

func (self *Set) AddPtr (m *Marking) {
	if slot, found := self.lookup(m); !found {
		self.data[slot] = m
	}
}

//### s := snk.MakeSet(&a, &b)
//... s.Len()
//=== 2

//### s := snk.MakeSet(&a, &b)
//... s.Add(c)
//... s.Add(c)
//... s.Len()
//=== 3

func (self Set) Get (m *Marking) (bool, *Marking) {
	if slot, found := self.lookup(m); found {
		return true, self.data[slot]
	} else {
		return false, nil
	}
}

func (self Set) Has (m *Marking) bool {
	found, _ := self.Get(m)
	return found
}

//+++ snk.MakeSet(&a, &b).Has(&a)
//+++ snk.MakeSet(&a, &b).Has(&b)
//--- snk.MakeSet(&a, &b).Has(&c)
