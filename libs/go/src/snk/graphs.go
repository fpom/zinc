package snk

import "hashstructure" 

type gnode struct {
	state Marking
	succs Set
}

type Graph struct {
	data map[uint64]gnode
}

func NewGraph () Graph {
	return Graph{make(map[uint64]gnode)}
}

func MakeGraph (markings ...Marking) Graph {
	graph := NewGraph()
	for _, m := range markings {
		graph.Add(m, NewSet())
	}
	return graph
}

func (self Graph) Empty () bool {
	return len(self.data) == 0
}

func (self Graph) Len () int {
	return len(self.data)
}

func (self Graph) lookup (m Marking) (uint64, bool) {
	slot, err := hashstructure.Hash(m.data, nil)
	if err != nil {
		panic(err)
	}
	perturb := slot
	for true {
		if value, found := self.data[slot]; !found {
			return slot, false
		} else if value.state.Eq(m) {
			return slot, true
		} else {
			slot = (5 * slot) + 1 + perturb
			perturb >>= 5
		}
	}
	return 0, false
}

func (self Graph) Add (m Marking, s Set) {
	slot, found := self.lookup(m)
	if ! found {
		self.data[slot] = gnode{m, s}
	}
}

func (self Graph) AddArcs (m Marking, s Set) {
	slot, found := self.lookup(m)
	if ! found {
		self.data[slot] = gnode{m, NewSet()}
	}
	self.data[slot].succs.Update(s)
}
