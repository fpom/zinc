package snk

import "os"
import "fmt"

func Main (name string, init func()*Marking, addsucc func(*Marking, *Set)) {
	const GRAPH = 1
	const MARKS = 2
	const LOCKS = 3
	size := false
	mode := 0
    for _, a := range os.Args[1:] {
		switch a {
		case "-s" : size = true
		case "-d" : mode = LOCKS
		case "-g" : mode = GRAPH
		case "-m" : mode = MARKS
		case "-h" :
			fmt.Println("usage: ", name, " [-s] (-d|-g|-m|-h)")
			fmt.Println("  options:")
			fmt.Println("    -s   only show size")
			fmt.Println("    -g   full marking graph")
			fmt.Println("    -d   deadlocks")
			fmt.Println("    -m   only markings")
			return
		default:
			fmt.Println("invalid option ", a, ", try -h for help")
			return
		}
    }
	if mode == 0 {
		fmt.Println("missing option, try -h for help")
		return
	}
	g := StateSpace(init, addsucc)
	if mode < LOCKS && size {
		fmt.Println(len(*g), " reachable states")
	} else if mode == LOCKS && size {
		count := 0
		for _, succ := range *g {
			if succ.Empty() {
				count += 1
			}
		}
		fmt.Println(count, " deadlocks")
	} else if mode == GRAPH {
		Println(g)
	} else {
		num := 0
		for state, succ := range *g {
			if mode == MARKS || succ.Empty() {
				fmt.Printf("[%d] ", num)
				state.Println()
				num += 1
			}
		}
	}
}
