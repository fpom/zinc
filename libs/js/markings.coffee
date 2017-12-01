dicts = require "./dicts"
msets = require "./multisets"

class BlackToken
    toString: -> "dot"
    hash: -> 2881495479
    eq: (other) -> other is this

dot = new BlackToken()

class Marking
    constructor: (@id=null) ->
        """
        coffee> new markings.Marking()
        Marking { id: null, d: Dict { indices: {}, itemlist: [], used: 0 } }
        coffee> new markings.Marking(42)
        Marking { id: 42, d: Dict { indices: {}, itemlist: [], used: 0 } }
        """
        @d = new dicts.Dict()
    iter: ->
        return @d.iter()
    hash: ->
        """
        coffee> a = new markings.Marking()
        coffee> a.set("p1", 1, 2, 3)
        coffee> a.set("p2", 4, 5)
        coffee> b = new markings.Marking()
        coffee> b.set("p1", 3, 1, 2)
        coffee> b.set("p2", 5, 4)
        coffee> a.hash() == b.hash()
        true
        """
        h = 7028009221
        for [p, m] from @d.iter()
            h ^= (dicts.hash(p) << 5) + dicts.hash(m)
        return h
    eq: (other) ->
        """
        coffee> a = new markings.Marking()
        coffee> a.set("p1", 1, 2, 3)
        coffee> a.set("p2", 4, 5)
        coffee> b = new markings.Marking()
        coffee> b.set("p1", 3, 1, 2)
        coffee> b.set("p2", 5, 4)
        coffee> a.eq(b)
        true
        """
        if other not instanceof Marking
            return false
        return @d.eq(other.d)
    copy: (id=null) ->
        """
        coffee> a = new markings.Marking()
        coffee> a.set("p1", 1, 2, 3)
        coffee> a.set("p2", 4, 5)
        coffee> a.copy().eq(a)
        coffee> a.copy() is a
        false
        """
        copy = new Marking(id)
        for [p, m] from @iter()
            copy.d.set(p, m.copy())
        return copy
    has: (place) ->
        """
        coffee> a = new markings.Marking()
        coffee> a.set("p1", 1, 2, 3)
        coffee> a.set("p2", 4, 5)
        coffee> a.has("p1")
        true
        coffee> a.has("p3")
        false
        """
        return @d.has(place)
    set: (place, tokens...) ->
        """
        coffee> a = new markings.Marking()
        coffee> a.set("p1", 1, 2, 3)
        coffee> console.log a.get("p1").toString()
        [1, 2, 3]
        coffee> a.set("p1")
        coffee> a.has("p1")
        false
        """
        if tokens.length == 0 and @has(place)
            @d.del(place)
        else
            @d.set(place, new msets.Mset(tokens...))
    update: (place, tokens) ->
        """
        coffee> a = new markings.Marking()
        coffee> a.set("p1", 1, 2, 3)
        coffee> a.set("p2", 4, 5, 6)
        coffee> a.update("p1", a.get("p2"))
        coffee> console.log a.get("p1").toString()
        [1, 2, 3, 4, 5, 6]
        """
        if @has(place)
            @d.get(place).add(tokens)
        else
            @d.set(place, tokens.copy())
    get: (place) ->
        """
        coffee> a = new markings.Marking()
        coffee> a.set("p1", 1, 2, 3)
        coffee> console.log a.get("p1").toString()
        [1, 2, 3]
        coffee> console.log a.get("p2").toString()
        []
        """
        return @d.get(place, new msets.Mset())
    empty: (place) ->
        """
        coffee> a = new markings.Marking()
        coffee> a.set("p1", 1, 2, 3)
        coffee> a.empty("p1")
        false
        coffee> a.empty("p2")
        true
        """
        return @get(place).empty()
    add: (other) ->
        """
        coffee> a = new markings.Marking()
        coffee> a.set("p1", 1, 2, 3)
        coffee> b = new markings.Marking()
        coffee> b.set("p1", 4)
        coffee> b.set("p2", 5, 6)
        coffee> c = new markings.Marking()
        coffee> c.set("p1", 1, 2, 3, 4)
        coffee> c.set("p2", 5, 6)
        coffee> a.add(b).eq(c)
        true
        """
        for [p, m] from other.iter()
            @update(p, m)
        return this
    sub: (other) ->
        """
        coffee> a = new markings.Marking()
        coffee> a.set("p1", 1, 2, 3)
        coffee> b = new markings.Marking()
        coffee> b.set("p1", 2, 3)
        coffee> b.set("p2", 5)
        coffee> c = new markings.Marking()
        coffee> c.set("p1", 1)
        coffee> a.sub(b).eq(c)
        true
        """
        for [p, m] from other.iter()
            mine = @d.get(p, this)
            if mine is this
                # skip
            else if m.geq(mine)
                @d.del(p)
            else
                @d.set(p, mine.sub(m))
        return this
    geq: (other) ->
        """
        coffee> a = new markings.Marking()
        coffee> a.set("p1", 1, 2, 3)
        coffee> b = new markings.Marking()
        coffee> b.set("p1", 2, 3)
        coffee> a.geq(b)
        true
        coffee> b.set("p1", 1, 2, 3)
        coffee> a.geq(b)
        true
        coffee> b.set("p1", 1, 2, 3, 4)
        coffee> b.get("p1").d
        coffee> a.geq(b)
        false
        coffee> b.set("p1", 1, 2, 3)
        coffee> b.set("p2", 4)
        coffee> a.geq(b)
        false
        """
        for [p, m] from other.iter()
            if not @get(p).geq(m)
                return false
        return true
    toString: ->
        """
        coffee> a = new markings.Marking()
        coffee> a.set("p1", 1, 2, 3)
        coffee> a.set("p2", 3, 4)
        coffee> console.log a.toString()
        {'p1': [1, 2, 3], 'p2': [3, 4]}
        """
        items = ("'#{ p }': #{ m.toString() }" for [p, m] from @iter())
        if @id != null
            return "[#{ @id }] {#{ items.join(', ') }}"
        else
            return "{#{ items.join(', ') }}"

module.exports =
    Marking: Marking
    dot: dot
    BlackToken: BlackToken
