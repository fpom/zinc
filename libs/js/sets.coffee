dicts = require "./dicts"

class Set
    constructor: (markings...) ->
        @d = new dicts.Dict()
        for m in markings
            @add(m)
    empty: ->
        return @d.empty()
    len: ->
        return @d.len()
    add: (marking) ->
        @d.set(marking, null)
    get: (marking) ->
        return @d.getitem(marking)[0]
    has: (marking) ->
        return @d.has(marking)
    iter: ->
        for [m, _] from @d.iter()
            yield m

class QueueError
    constructor: (@message) ->
        @name = "QueueError"

class Queue
    constructor: (markings...) ->
        @data = {}
        @head = 0
        @tail = 0
        for m in markings
            @put(m)
    empty: ->
        return @head == @tail
    full: ->
        return @head == @tail+1
    put: (marking) ->
        if @full()
            throw new QueueError("cannot put on full queue")
        @data[@tail] = marking
        @tail++
    get: ->
        if @empty()
            throw new QueueError("cannot get from empty queue")
        m = @data[@head]
        delete @data[@head]
        @head++
        return m

module.exports =
    Set: Set
    QueueError: QueueError
    Queue: Queue
