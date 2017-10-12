package snk

import "fmt"

type MarkingGraph map[*Marking]*Set

func StateSpace (init func()*Marking, addsucc func(*Marking, *Set)) *MarkingGraph {
	todo := MakeSet(init())
	done := NewSet()
	succ := NewSet()
	graph := make(MarkingGraph)
	for state_ := todo.Pop(); state_ != nil; state_ = todo.Pop() {
		state := state_.(*Marking)
		done.Add(state)
		addsucc(state, succ)
		graph[state] = succ.Copy()
		for s := succ.Pop(); s != nil; s = succ.Pop() {
			if ! (done.Has(s) || todo.Has(s)) {
				todo.Add(s)
			}
		}
	}
	return &graph
}

func Reachable (init func()*Marking, addsucc func(*Marking, *Set)) *Set {
	graph := StateSpace(init, addsucc)
	reach := NewSet()
	for state, _ := range *graph {
		reach.Add(state)
	}
	return reach
}

func DeadLocks (init func()*Marking, addsucc func(*Marking, *Set)) *Set {
	graph := StateSpace(init, addsucc)
	dead := NewSet()
	for state, succ := range *graph {
		if succ.Empty() {
			dead.Add(state)
		}
	}
	return dead
}

func Println (graph *MarkingGraph) {
	i := 0
	for state, succ := range *graph {
		fmt.Printf("[%d] ", i)
		i += 1
		state.Println()
		for s := range succ.Iter() {
			fmt.Print(">>> ")
			s.(*Marking).Println()
		}
	}
}
