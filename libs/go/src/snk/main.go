package snk

import "os"
import "fmt"

func StateSpace (init func()Marking, addsucc func(Marking, Set),
	print_states bool, print_succs bool) int {
	var succ Set
	count := 0
	i := init()
	todo := MakeQueue(&i)
	seen := MakeSet(&i)
	for ! todo.Empty() {
		state := todo.Get()
		if print_states {
			fmt.Println(*state)
		}
		succ = MakeSet()
		addsucc(*state, succ)
		for _, s := range succ.data {
			if found, p := seen.Get(s); found {
				s = p
			} else {
				count += 1
				s.SetId(count)
				seen.AddPtr(s)
				todo.Put(s)
			}
			if print_succs {
				fmt.Println(" >", *s)
			}
		}
	}
	return count
}

func DeadLocks (init func()Marking, addsucc func(Marking, Set), print bool) int {
	// var succ Set
	// count := 0
	// i := init()
	// todo := append(make([]*Marking, 0), &i)
	// seen := MakeSet(i)
	// for len(todo) > 0 {
	// 	state := todo[0]
	// 	todo = todo[1:]
	// 	succ = MakeSet()
	// 	addsucc(*state, succ)
	// 	if succ.Empty() {
	// 		if print {
	// 			fmt.Printf("[%d] %s", count, state)
	// 		}
	// 		count += 1
	// 	} else {
	// 		for _, s := range *succ.data {
	// 			if ! seen.Has(*s) {
	// 				seen.Add(*s)
	// 				todo = append(todo, s)
	// 			}
	// 		}
	// 	}
	// }
	// return count
	return 0
}

func LabelledTransitionsSystem (init func()Marking, itersucc SuccIterFunc) {
	// count := 0
	// i := init()
	// todo := append(make([]*Marking, 0), &i)
	// seen := MakeSet(i)
	// for len(todo) > 0 {
	// 	state := todo[0]
	// 	todo = todo[1:]
	// 	fmt.Printf("[%d] %s\n", count, state)
	// 	count += 1
	// 	for i, p := Iter(itersucc, *state); p != nil; p = i.Next() {
	// 		// print trans & mode
	// 		fmt.Print("@ ", p.Name, " = {")
	// 		first := true
	// 		for key, val := range p.Mode {
	// 			if first {
	// 				first = false
	// 			} else {
	// 				fmt.Print(", ")
	// 			}
	// 			fmt.Printf("'%s': ", key)
	// 			fmt.Print(val)
	// 		}
	// 		fmt.Println("}")
	// 		// print markings
	// 		fmt.Println(" - ", p.Sub)
	// 		fmt.Println(" + ", p.Add)
	// 		s := state.Copy().Sub(p.Sub).Add(p.Add)
	// 		fmt.Println(" > ", s)
	// 		if ! seen.Has(s) {
	// 			seen.Add(s)
	// 			todo = append(todo, &s)
	// 		}
	// 	}
	// }
}

func Main (name string, init func()Marking,
	addsucc func(Marking, Set), itersucc SuccIterFunc) {
	const GRAPH = 1
	const MARKS = 2
	const LTS = 3
	const LOCKS = 4
	size := false
	mode := 0
    for _, a := range os.Args[1:] {
		switch a {
		case "-s" : size = true
		case "-d" : mode = LOCKS
		case "-g" : mode = GRAPH
		case "-m" : mode = MARKS
		case "-l" : mode = LTS
		case "-h" :
			fmt.Println("usage: ", name, " [-s] (-d|-g|-m|-l|-h)")
			fmt.Println("  options:")
			fmt.Println("    -l   print labelled transitions system")
			fmt.Println("    -g   print marking graph")
			fmt.Println("    -m   only print markings")
			fmt.Println("    -d   only print deadlocks")
			fmt.Println("    -s   only print size")
			fmt.Println("    -h   print help and exit")
			return
		default:
			fmt.Println("invalid option ", a, ", try -h for help")
			return
		}
    }
	if mode == 0 {
		fmt.Println("missing option, try -h for help")
	} else if mode < LOCKS && size {
		count := StateSpace(init, addsucc, false, false)
		fmt.Println(count, " reachable states")
	} else if mode == LOCKS && size {
		count := DeadLocks(init, addsucc, false)
		fmt.Println(count, " deadlocks")
	} else if mode == GRAPH {
		StateSpace(init, addsucc, true, true)
	} else if mode == MARKS {
		StateSpace(init, addsucc, true, false)
	} else if mode == LOCKS {
		DeadLocks(init, addsucc, true)
	} else if mode == LTS {
		LabelledTransitionsSystem(init, itersucc)
	}
}
