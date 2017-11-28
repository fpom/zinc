# Python3 dicts ported to CoffeeScript, inspired from a Python version at
# https://code.activestate.com/recipes/578375/

FREE  = -1
DUMMY = -2

hash = (obj) ->
    try
        return obj.hash()
    catch err
        h = 0
        if typeof(obj) == "string"
            for c in obj
                h = (h << 5) - h + c.charCodeAt(0)
        else if obj instanceof Array
            for x in obj
                h = (h << 5) - h + hash(x)
        else if obj instanceof Object
            for k, v of obj
                h = h ^ ((hash(k) << 5) - h + hash(v))
        else
            h = hash("#{obj}")
        return h

eq = (left, right) ->
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
        @clear()
        for key, val of init
            @set(key, val)
    clear: ->
        @indices  = {}
        @itemlist = []
        @used     = 0
    len: ->
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
        hashvalue = hash(key)
        [index, i] = @_lookup(key, hashvalue)
        if index < 0
            @indices[i] = @used
            @itemlist.push {key: key, value: value, hash: hashvalue}
            @used++
        else
            @itemlist[index] = {key: key, value: value, hash: hashvalue}
    get: (key) ->
        [index, i] = @_lookup(key, hash(key))
        if index < 0
            throw new KeyError("key #{key} not found")
        return @itemlist[index].value
    del: (key) ->
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
    has: (key) ->
        [index, i] = @_lookup(key, hash(key))
        return index >= 0
    get: (key, otherwise=null) ->
        [index, i] = @_lookup(key, hash(key))
        if index < 0
            return otherwise
        return @itemlist[index].value
    pop: ->
        if @user == 0
            throw new KeyError("cannot pop from empty dict")
        item = @itemlist[@itemlist.length - 1]
        @del(key)
        return [item.key, item.value]
    toString: ->
        items = ("#{ k }: #{ v }" for [k, v] from @iter())
        return "{#{ items.join(', ') }}"

module.exports =
    hash: hash
    eq: eq
    KeyError: KeyError
    Dict: Dict
