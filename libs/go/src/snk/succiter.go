package snk

import "time"
import "fmt"

type Binding map[string]interface{}

type Event struct {
	Name string
	Mode Binding
	Sub Marking
	Add Marking
}

type SuccIterator struct {
	done bool
	ask chan bool
	rep chan *Event
}

func (self SuccIterator) Next () *Event {
	var rep *Event
	if self.done {
		return nil
	}
	self.ask <- true
	rep = <- self.rep
	if rep == nil {
		self.done = true
	}
	return rep
}

func (self SuccIterator) Put (ev *Event) bool {
	if self.done {
		return false
	}
	if <- self.ask {
		self.rep <- ev
	} else {
		return false
	}
	if ev == nil {
		self.done = true
	}
	return true
}

func (self SuccIterator) Stop() {
	if ! self.done {
		self.ask <- false
		self.done = true
	}
}

type SuccIterFunc func (Marking, SuccIterator)

func Iter (fun SuccIterFunc, mk Marking) (SuccIterator, *Event) {
	it := SuccIterator{false, make(chan bool), make(chan *Event)}
	go fun(mk, it)
	return it, it.Next()
}

func test_iterator (state Marking, it SuccIterator) {
	empty := make(Binding)
    for i:= 0; i < 5; i++ {
		if ! it.Put(&Event{fmt.Sprintf("%d", i), empty, state, state}) {
            time.Sleep(10 * time.Millisecond)
            fmt.Println("stopped")
			return
        }
    }
    fmt.Println("finished")
    it.Put(nil)
}

func TestSuccIterator () {
    for i, p := Iter(test_iterator, NewMarking()); p != nil; p = i.Next() {
        fmt.Printf("%s ", p.Name)
    }
    time.Sleep(20 * time.Millisecond)
    for i, p := Iter(test_iterator, NewMarking()); p != nil; p = i.Next() {
        if p.Name == "3" {
            i.Stop()
			time.Sleep(10 * time.Millisecond)
            break
        }
        fmt.Printf("%s ", p.Name)
    }
	time.Sleep(20 * time.Millisecond)
}

//### snk.TestSuccIterator()
//... nil
//=== 0 1 2 3 4 finished
//=== 0 1 2 stopped
