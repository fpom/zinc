# Python3 dicts ported to CoffeeScript, inspired from a Python version at
# https://code.activestate.com/recipes/578375/

FREE  = -1
DUMMY = -2

hash = (obj) ->
    """
    coffee> dicts.hash("hello world")
    -8572760634
    coffee> dicts.hash(42)
    -4720677242
    coffee> dicts.hash(42) == dicts.hash("42")
    false
    coffee> dicts.hash([1, 2, 3])
    4097603114
    coffee> dicts.hash([1, 2, 3]) == dicts.hash([3, 2, 1])
    false
    coffee> dicts.hash(a:1, b:2, c:3)
    2146137064
    coffee> dicts.hash(a:1, b:2, c:3) == dicts.hash(c:3, b:2, a:1)
    true
    """
    try
        return obj.hash()
    catch err
        h = 0
        if typeof(obj) == "string"
            for c in "#{typeof obj}/#{obj}"
                h = (h << 5) - h + c.charCodeAt(0)
        else if obj instanceof Array
            for x in obj
                h = (h << 5) - h + hash(x)
        else if obj instanceof Object
            for k, v of obj
                h ^= ((hash(k) << 5) + hash(v))
        else
            h = hash("#{typeof obj}/#{obj}")
        return h

eq = (left, right) ->
    """
    coffee> dicts.eq("hello", "hello")
    true
    coffee> dicts.eq("hello", "world")
    false
    coffee> dicts.eq(42, 42)
    true
    coffee> dicts.eq(42, -42)
    false
    coffee> dicts.eq([1, 2, 3], [1, 2, 3])
    true
    coffee> dicts.eq([1, 2, 3], [1, 2, 3, 4])
    false
    coffee> dicts.eq([1, 2, 3], [1, 2, 4])
    false
    coffee> dicts.eq({a:1, b:2, c:3}, {c:3, b:2, a:1})
    true
    coffee> dicts.eq({a:1, b:2, c:3}, {a:1, b:2, c:3, d:4})
    false
    coffee> dicts.eq({a:1, b:2, c:3}, {a:1, b:2})
    false
    coffee> dicts.eq({a:1, b:2, c:3}, {a:1, b:2, c:1234})
    false
    coffee> dicts.eq({a:1, b:2, c:3}, {a:1, b:2, d:3})
    false
    """
    try
        return left.eq(right)
    catch err
        if left instanceof Array
            if right not instanceof Array
                return false
            if right.length != left.length
                return false
            for i in [0..left.length]
                if not eq(left[i], right[i])
                    return false
            return true
        else if left instanceof Object
            if right not instanceof Object
                return false
            for k, v of left
                if not right[k]?
                    return false
            for k, v of right
                if not eq(left[k], right[k])
                    return false
            return true
        else
            return left == right

class KeyError
    constructor: (@message) ->
        @name = "KeyError"

class Dict
    constructor: (init={}) ->
        """
        coffee> new dicts.Dict()
        Dict { indices: {}, itemlist: [], used: 0 }
        coffee> new dicts.Dict(a:1, b:2)
        Dict{indices: { '...': 1, '...': 0 },
             itemlist: [{ key: 'a', value: 1, hash: ...},
                        { key: 'b', value: 2, hash: ...}],
             used: 2}
        """
        @clear()
        for key, val of init
            @set(key, val)
    clear: ->
        @indices  = {}
        @itemlist = []
        @used     = 0
    len: ->
        """
        coffee> (new dicts.Dict()).len()
        0
        coffee> (new dicts.Dict(a:1, b:2)).len()
        2
        """
        return @used
    _gen_probes: (hashvalue) ->
        PERTURB_SHIFT = 5
        if hashvalue < 0
            hashvalue = -hashvalue
        i = hashvalue
        yield i
        perturb = hashvalue
        while true
            i = 5 * i + perturb + 1
            perturb >>= PERTURB_SHIFT
            yield i
    _lookup: (key, hashvalue) ->
        freeslot = null
        for i from @_gen_probes(hashvalue)
            index = @indices[i]
            if index == undefined
                index = FREE
                if freeslot == null
                    return [FREE, i]
                else
                    return [DUMMY, freeslot]
            else if index == DUMMY
                if freeslot == null
                    freeslot = i
            else
                item = @itemlist[index]
                if item.key is key || item.hash == hashvalue && eq(item.key, key)
                    return [index, i]
    set: (key, value) ->
        """
        coffee> a = new dicts.Dict(a:1, b:2)
        coffee> a.set("c", 3)
        coffee> a.set("a", 0)
        coffee> console.log a.toString()
        {a: 0, b: 2, c: 3}
        """
        hashvalue = hash(key)
        [index, i] = @_lookup(key, hashvalue)
        if index < 0
            @indices[i] = @used
            @itemlist.push {key: key, value: value, hash: hashvalue}
            @used++
        else
            @itemlist[index] = {key: key, value: value, hash: hashvalue}
    fetch: (key, otherwise=null) ->
        [index, i] = @_lookup(key, hash(key))
        if index < 0
            return otherwise
        return @itemlist[index].value
    get: (key, def=undefined) ->
        """
        coffee> a = new dicts.Dict(a:1, b:2)
        coffee> a.get("a")
        1
        coffee> a.get("x")
        Thrown: ...
        coffee> a.get("x", null)
        null
        """
        [index, i] = @_lookup(key, hash(key))
        if index < 0
            if def is undefined
                throw new KeyError("key #{key} not found")
            else
                return def
        return @itemlist[index].value
    del: (key) ->
        """
        coffee> a = new dicts.Dict(a:1, b:2)
        coffee> a.del("a")
        coffee> a.del("x")
        Thrown: ...
        coffee> a.eq(new dicts.Dict(b:2))
        true
        """
        [index, i] = @_lookup(key, hash(key))
        if index < 0
            throw new KeyError("key #{key} not found")
        @indices[i] = DUMMY
        @used--
        if index != @used
            lastitem = @itemlist[@itemlist.length - 1]
            [lastindex, j] = @_lookup(lastitem.key, lastitem.hash)
            @indices[j] = index
            @itemlist[index] = lastitem
        @itemlist.pop()
    iter: ->
        for item in @itemlist
            yield [item.key, item.value]
    copy: ->
        copy = new Dict()
        for item in @itemlist
            copy.set(item.key, item.value)
        return copy
    has: (key) ->
        [index, i] = @_lookup(key, hash(key))
        return index >= 0
    pop: ->
        if @user == 0
            throw new KeyError("cannot pop from empty dict")
        item = @itemlist[@itemlist.length - 1]
        @del(key)
        return [item.key, item.value]
    eq: (other) ->
        if other not instanceof Dict
            return false
        if @used != other.used
            return false
        for [k, v] from @iter()
            x = other.get(k, null)
            if x is null or not eq(v, x)
                return false
        return true
    toString: ->
        items = ("#{ k }: #{ v }" for [k, v] from @iter())
        return "{#{ items.join(', ') }}"

module.exports =
    hash: hash
    eq: eq
    KeyError: KeyError
    Dict: Dict
