package snk

import "time"
import "fmt"

type Event struct {
	Name string
	Mode map[string]interface{}
	Sub Marking
	Add Marking
}

type Iterator struct {
	ask chan bool
	rep chan *Event
}

type Iterable func (Marking, Iterator)

func First (it Iterable, mk Marking) (Iterator, *Event) {
	ret := Iterator{make(chan bool), make(chan *Event)}
	go it(mk, ret)
	return ret, ret.Get()
}

func (self Iterator) Get () *Event {
	self.ask <- true
	return <-self.rep
}

func (self Iterator) Stop () {
	self.ask <- false
}

func (self Iterator) Put (ev *Event) bool {
	ask := <-self.ask
	if ask {
		self.rep <- ev
	}
	return ask
}

func test_iterator (state Marking, pipe Iterator) {
	empty := make(map[string]interface{})
    for i:= 0; i < 5; i++ {
        if ! pipe.Put(&Event{fmt.Sprintf("%d", i), empty, state, state}) {
            time.Sleep(10 * time.Millisecond)
            fmt.Println("stopped")
            return
        }
    }
    fmt.Println("finished")
    pipe.Put(nil)
}

func TestIterator () {
    for it, ev := First(test_iterator, Marking{}); ev != nil; ev = it.Get() {
        fmt.Printf("%s ", ev.Name)
    }
    time.Sleep(20 * time.Millisecond)
    for it, ev := First(test_iterator, Marking{}); ev != nil; ev = it.Get() {
        if ev.Name == "3" {
            it.Stop()
			time.Sleep(10 * time.Millisecond)
            break
        }
        fmt.Printf("%s ", ev.Name)
    }
	time.Sleep(20 * time.Millisecond)
}

//### snk.TestIterator()
//... nil
//=== 0 1 2 3 4 finished
//=== 0 1 2 stopped
