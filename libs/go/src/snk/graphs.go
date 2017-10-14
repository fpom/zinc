package snk

import "hashstructure" 

type pair struct {
	state Marking
	succs Set
}

type Graph map[uint64]pair

func MakeGraph (markings ...Marking) Graph {
	graph := Graph{}
	for _, m := range markings {
		graph.Add(m, Set{})
	}
	return graph
}

func (self Graph) Empty () bool {
	return len(self) == 0
}

func (self Graph) Len () int {
	return len(self)
}

func (self Graph) lookup (m Marking) (uint64, bool) {
	slot, err := hashstructure.Hash(m, nil)
	if err != nil {
		panic(err)
	}
	perturb := slot
	for true {
		if value, found := self[slot]; !found {
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
		self[slot] = pair{m, s}
	}
}

func (self Graph) AddArcs (m Marking, s Set) {
	slot, found := self.lookup(m)
	if ! found {
		self[slot] = pair{m, Set{}}
	}
	self[slot].succs.Update(s)
}
