sets = require "./sets"
dicts = require "./dicts"

statespace = (init, addsucc, print_states, print_succs, print_dead) ->
    i = init()
    i.id = 0
    todo = new sets.Queue(i)
    seen = new sets.Set(i)
    dead = 0
    while not todo.empty()
        state = todo.get()
        succ = new sets.Set()
        addsucc(state, succ)
        if succ.empty()
            dead += 1
        if (print_dead and succ.empty()) or print_states
            console.log state.toString()
        for s from succ.iter()
            if seen.has(s)
                s = seen.get(s)
            else
                s.id = seen.len()
                seen.add(s)
                todo.put(s)
            if print_succs
                console.log ">", s.toString()
    return [seen.len(), dead]

dumpobj = (obj) ->
    return "{" + ("'#{ k }': #{ v }" for k, v of obj).join(", ") + "}"
  
lts = (init, itersucc) ->
    i = init()
    i.id = 0
    todo = new sets.Queue(i)
    seen = new sets.Set(i)
    while not todo.empty()
        state = todo.get()
        console.log state.toString()
        for [trans, mode, sub, add] from itersucc(state)
            succ = state.copy().sub(sub).add(add)
            if seen.has(succ)
                succ = seen.get(succ)
            else
                succ.id = seen.len()
                seen.add(succ)
                todo.put(succ)
            console.log "@ #{ trans } = #{ dumpobj(mode) }"
            console.log " - #{ sub.toString() }"
            console.log " + #{ add.toString() }"
            console.log " > #{ succ.toString() }"

main = (name, init, addsucc, itersucc) ->
    args = {s: false, d: false, m: false, g: false, l: false}
    for c in process.argv[2..].join("")
        if args[c]?
            args[c] = true
        else if c == "-"
            # skip
        else if c == "h"
            console.log "usage: #{ name } [-s] (-d|-g|-m|-l|-h)"
            console.log "  options:"
            console.log "    -l   labelled transitions system"
            console.log "    -g   print marking graph"
            console.log "    -m   only print markings"
            console.log "    -d   only print deadlocks"
            console.log "    -s   only print size"
            console.log "    -h   print help and exit"
            return
        else
            console.log "invalid option #{ c }, try -h for help"
            return
    if args.s
        [s, d] = statespace(init, addsucc, false, false, false)
        if args.d
            console.log "#{ d } deadlocks"
        else
            console.log "#{ s } reachable states"
    else if args.l
        lts(init, itersucc)
    else if args.g
        statespace(init, addsucc, true, true, false)
    else if args.m
        statespace(init, addsucc, true, false, false)
    else if args.d
        statespace(init, addsucc, false, false, true)
    else
        console.log "missing option, try -h for help"

module.exports =
    statespace: statespace
    lts: lts
    main: main
