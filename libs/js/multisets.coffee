dicts = require "./dicts"

class Mset
    constructor: (items...) ->
        @d = new dicts.Dict()
        for i in items
            @d.set(i, @d.get(i, 0) + 1)
    iter: ->
        
    iterdup: ->
        
    toString: ->
        items = ("#{ v }" for v from @iterdup())
        return "[#{ items.join(', ') }]"

m = new Mset(1, 2, 2, 3, 3, 3)
console.log m.d
