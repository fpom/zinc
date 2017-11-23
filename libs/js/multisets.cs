class Multiset
    constructor: (content...) ->
        @content = {}
        for item in content
            if @content[item]?
                @content[item]++
            else
                @content[item] = 1
    eq: (other) ->
        for item, count of other.content
            if @content[item]?
                if @content[item] != count
                    return false
            else
                return false
        return true            

a = new Multiset(1, 2, 2, 3, 3, 3)
b = new Multiset(2, 3, 2, 3, 1, 3)
c = new Multiset(1, 2, 2, 3)

console.log(new Multiset([1,2]))
console.log(a.eq(b))
console.log(a.eq(c))
