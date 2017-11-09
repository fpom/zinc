package snk

import "os"
import "fmt"

func Main (name string, init func()Marking, addsucc func(Marking, Set)) {
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
			fmt.Println("    -s   only print size")
			fmt.Println("    -g   print full marking graph")
			fmt.Println("    -m   only print markings")
			fmt.Println("    -d   only print deadlocks")
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
		fmt.Println(g.Len(), " reachable states")
	} else if mode == LOCKS && size {
		count := 0
		for _, p := range g.data {
			if p.succs.Empty() {
				count += 1
			}
		}
		fmt.Println(count, " deadlocks")
	} else if mode == GRAPH {
		fmt.Printf("INIT ")
		init().Println()
		Println(g)
	} else {
		fmt.Printf("INIT ")
		init().Println()
		num := 0
		for _, p := range g.data {
			if mode == MARKS || p.succs.Empty() {
				fmt.Printf("[%d] ", num)
				p.state.Println()
				num += 1
			}
		}
	}
}
