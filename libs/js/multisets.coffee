dicts = require "./dicts"

class Mset
    constructor: (items...) ->
        """
        coffee> new multisets.Mset(1, 2, 3)
        Mset{d: Dict{indices: {...}, itemlist: [..., ..., ...], used: 3}}
        """
        @d = new dicts.Dict()
        for i in items
            @d.set(i, @d.get(i, 0) + 1)
    iter: ->
        """
        coffee> (i for i from new multisets.Mset(1, 2, 2, 3, 3, 3).iter())
        [ 1, 2, 3 ]
        coffee> (i for i from new multisets.Mset().iter())
        []
        """
        for [k, n] from @d.iter()
            yield k
    iterdup: ->
        """
        coffee> (i for i from new multisets.Mset(1, 2, 2, 3, 3, 3).iterdup())
        [ 1, 2, 2, 3, 3, 3 ]
        coffee> (i for i from new multisets.Mset().iterdup())
        []
        """
        for [k, n] from @d.iter()
            for i in [1..n]
                yield k
    hash: ->
        """
        coffee> a = new multisets.Mset(1, 2, 2, 3, 3, 3)
        coffee> b = new multisets.Mset(3, 2, 3, 2, 3, 1)
        coffee> c = new multisets.Mset(1, 2, 3)
        coffee> a.hash() == b.hash()
        true
        coffee> a.hash() == c.hash()
        false
        """
        h = 2485867687
        for [k, n] from @d.iter()
            h ^= (dicts.hash(k) << 5) + dicts.hash(n)
        return h
    eq: (other) ->
        """
        coffee> a = new multisets.Mset(1, 2, 2, 3, 3, 3)
        coffee> b = new multisets.Mset(3, 2, 3, 2, 3, 1)
        coffee> c = new multisets.Mset(1, 2, 3)
        coffee> a.eq(b)
        true
        coffee> a.eq(c)
        false
        coffee> (new multisets.Mset()).eq(new multisets.Mset())
        true
        """
        if other not instanceof Mset
            return false
        return @d.eq(other.d)
    copy: ->
        """
        coffee> a = new multisets.Mset(1, 2, 2, 3, 3, 3)
        coffee> a.eq(a.copy())
        true
        coffee> a is a.copy()
        false
        """
        return new Mset(@iterdup()...)
    len: ->
        """
        coffee> (new multisets.Mset()).len()
        0
        coffee> (new multisets.Mset(1, 2, 2, 3, 3, 3)).len()
        6
        """
        len = 0
        for [k, n] from @d.iter()
            len += n
        return len
    add: (other) ->
        """
        coffee> a = new multisets.Mset(1, 2, 3)
        coffee> b = new multisets.Mset(2, 3, 3)
        coffee> a.add(b)
        coffee> a.eq(new multisets.Mset(1, 2, 2, 3, 3, 3))
        true
        """
        for [k, n] from other.d.iter()
            @d.set(k, @d.get(k, 0) + n)
        return this
    sub: (other) ->
        """
        coffee> a = new multisets.Mset(1, 2, 2, 3, 3, 3)
        coffee> b = new multisets.Mset(2, 3, 3)
        coffee> c = new multisets.Mset(1, 2, 3)
        coffee> d = new multisets.Mset(1, 2, 2, 3, 3, 3)
        coffee> a.sub(b)
        coffee> a.eq(c)
        true
        coffee> a.sub(c).len()
        0
        coffee> c.sub(d).len()
        0
        """
        for [k, n] from other.d.iter()
            m = @d.get(k, 0)
            if m <= n
                @d.del(k)
            else
                @d.set(k, m - n)
        return this
    geq: (other) ->
        """
        coffee> a = new multisets.Mset(1, 2, 2, 3, 3, 3)
        coffee> b = new multisets.Mset(2, 3, 3)
        coffee> c = new multisets.Mset(1, 2, 3)
        coffee> a.geq(b)
        true
        coffee> b.geq(c)
        false
        """
        for [k, n] from other.d.iter()
            if not @d.get(k, 0) >= n
                return false
        return true
    empty: ->
        """
        coffee> a = new multisets.Mset(1, 2, 2, 3, 3, 3)
        coffee> b = new multisets.Mset()
        coffee> a.empty()
        false
        coffee> b.empty()
        true
        """
        return @d.used == 0
    count: (value) ->
        """
        coffee> a = new multisets.Mset(1, 2, 2, 3, 3, 3)
        coffee> (a.count(i) for i in [0...4])
        [ 0, 1, 2, 3 ]        
        """
        return @d.get(value, 0)
    map: (func) ->
        """
        coffee> a = new multisets.Mset(1, 2, 2, 3, 3, 3)
        coffee> b = a.map((k, n) -> [k+1, n+1])
        coffee> b.eq(new multisets.Mset(2, 2, 3, 3, 3, 4, 4, 4, 4))
        true
        """
        copy = new Mset()
        for [k, n] from @d.iter()
            copy.d.set(func(k, n)...)
        return copy
    toString: ->
        """
        coffee> console.log new multisets.Mset(1, 2, 2, 3, 3, 3).toString()
        [1, 2, 2, 3, 3, 3]
        coffee> console.log new multisets.Mset().toString()
        []
        """
        items = ("#{ v }" for v from @iterdup())
        return "[#{ items.join(', ') }]"

module.exports =
    Mset: Mset
