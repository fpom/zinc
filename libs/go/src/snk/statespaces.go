package snk

import "fmt"

func StateSpace (init func()Marking, addsucc func(Marking, Set)) Graph {
	todo := MakeSet(init())
	done := NewSet()
	succ := NewSet()
	graph := NewGraph()
	for todo.NotEmpty() {
		state := todo.Pop()
		done.Add(state)
		addsucc(state, succ)
		graph.AddArcs(state, succ)
		for succ.NotEmpty() {
			s := succ.Pop()
			if ! (done.Has(s) || todo.Has(s)) {
				todo.Add(s)
			}
		}
	}
	return graph
}

func Reachable (init func()Marking, addsucc func(Marking, Set)) Set {
	graph := StateSpace(init, addsucc)
	reach := NewSet()
	for _, p := range graph.data {
		reach.Add(p.state)
	}
	return reach
}

func DeadLocks (init func()Marking, addsucc func(Marking, Set)) Set {
	graph := StateSpace(init, addsucc)
	dead := NewSet()
	for _, p := range graph.data {
		if p.succs.Empty() {
			dead.Add(p.state)
		}
	}
	return dead
}

func Println (graph Graph) {
	i := 0
	for _, p := range graph.data {
		fmt.Printf("[%d] ", i)
		i += 1
		p.state.Println()
		for _, s := range p.succs.data {
			fmt.Print(" > ")
			s.Println()
		}
	}
}
