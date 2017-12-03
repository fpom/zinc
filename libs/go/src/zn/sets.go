package zn

type Set struct {
	data map[uint64]*Marking
}

//*** a := zn.MakeMarking()
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

//+++ zn.MakeSet().Empty()
//--- zn.MakeSet(&a).Empty()
//--- zn.MakeSet().NotEmpty()
//+++ zn.MakeSet(&a).NotEmpty()

func (self Set) Len () int {
	return len(self.data)
}

//+++ zn.MakeSet().Len() == 0
//+++ zn.MakeSet(&a).Len() == 1
//+++ zn.MakeSet(&a, &a).Len() == 1

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

//### s := zn.MakeSet(&a, &b)
//... s.Len()
//=== 2

//### s := zn.MakeSet(&a, &b)
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

//+++ zn.MakeSet(&a, &b).Has(&a)
//+++ zn.MakeSet(&a, &b).Has(&b)
//--- zn.MakeSet(&a, &b).Has(&c)
