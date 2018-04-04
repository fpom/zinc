package zn

type Queue struct {
	head uint64
	tail uint64
	data map[uint64]*Marking
}

func MakeQueue (markings ...Marking) Queue {
	q := Queue{0, 0, make(map[uint64]*Marking)}
	for _, m := range markings {
		q.Put(m)
	}
	return q
}

func (self Queue) Empty () bool {
	return self.head == self.tail
}

func (self Queue) Full () bool {
	return self.head == self.tail+1
}

func (self *Queue) Put (m Marking) {
	if self.Full() {
		panic("queue is full")
	}
	self.data[self.tail] = &m
	self.tail++
}

func (self *Queue) Get () Marking {
	if self.Empty() {
		panic("queue is empty")
	}
	m := self.data[self.head]
	delete(self.data, self.head)
	self.head++
	return *m
}
