package snk

import "fmt"

func StateSpace (init func()Marking, addsucc func(Marking, Set)) Graph {
	todo := MakeSet(init())
	done := Set{}
	succ := Set{}
	graph := Graph{}
	for state := todo.Pop(); state != nil; state = todo.Pop() {
		done.Add(state)
		addsucc(state, succ)
		graph.AddArcs(state, succ)
		for s := succ.Pop(); s != nil; s = succ.Pop() {
			if ! (done.Has(s) || todo.Has(s)) {
				todo.Add(s)
			}
		}
	}
	return graph
}

func Reachable (init func()Marking, addsucc func(Marking, Set)) Set {
	graph := StateSpace(init, addsucc)
	reach := Set{}
	for _, p := range graph {
		reach.Add(p.state)
	}
	return reach
}

func DeadLocks (init func()Marking, addsucc func(Marking, Set)) Set {
	graph := StateSpace(init, addsucc)
	dead := Set{}
	for _, p := range graph {
		if p.succs.Empty() {
			dead.Add(p.state)
		}
	}
	return dead
}

func Println (graph Graph) {
	i := 0
	for _, p := range graph {
		fmt.Printf("[%d] ", i)
		i += 1
		p.state.Println()
		for _, s := range p.succs {
			fmt.Print(">>> ")
			s.Println()
		}
	}
}
