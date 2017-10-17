import operator, functools
from collections import Counter

def hashable (cls) :
    def __hash__ (self) :
        if not hasattr(self, "_hash") :
            self._hash = functools.reduce(operator.xor,
                                          (hash(i) for i in self._hash_items()),
                                          hash(cls.__name__))
        return self._hash
    cls.__hash__ = __hash__
    def unhash (self) :
        if hasattr(self, "_hash") :
            delattr(self, "_hash")
    cls.unhash = unhash
    return cls

def mutation (old, name=None) :
    @functools.wraps(old, assigned=("__name__", "__doc__"))
    def new (self, *l, **k) :
        if hasattr(self, "_hash") :
            raise ValueError("hashed %s object is not mutable"
                             % self.__class__.__name__)
        return old(self, *l, **k)
    return new

@hashable
class hdict (dict) :
    def _hash_items (self) :
        return self.items()
    __delitem__ = mutation(dict.__delitem__)
    __setitem__ = mutation(dict.__setitem__)
    clear = mutation(dict.clear)
    pop = mutation(dict.pop)
    popitem = mutation(dict.popitem)
    setdefault = mutation(dict.setdefault)
    update = mutation(dict.update)
    def copy (self) :
        return self.__class__(self)

class record (object) :
    def __init__ (self, content={}, **attrs) :
        content = dict(content, **attrs)
        self.__dict__["_fields"] = set(content)
        self.__dict__.update(content)
    def __setattr__ (self, name, value) :
        self.__dict__[name] = value
        self._fields.add(name)
    def asdict (self) :
        return {name : getattr(self, name) for name in self._fields}
    def copy (self) :
        return self.__class__(self.asdict())
    def __add__ (self, other) :
        return self.__class__(self.asdict(), **other.asdict())


def iterate (value) :
    """Like Python's builtin `iter` but consider strings as atomic.

    >>> list(iter([1, 2, 3]))
    [1, 2, 3]
    >>> list(iterate([1, 2, 3]))
    [1, 2, 3]
    >>> list(iter('foo'))
    ['f', 'o', 'o']
    >>> list(iterate('foo'))
    ['foo']

    @param value: any object
    @type value: `object`
    @return: an iterator on the elements of `value` if is is iterable
        and is not string, an iterator on the sole `value` otherwise
    @rtype: `generator`
    """
    if isinstance(value, (str, bytes)) :
        return iter([value])
    else :
        try :
            return iter(value)
        except TypeError :
            return iter([value])

def flatten (value) :
    """Flatten a nest of lists and tuples.
    Like `iterate`, `flattent` does not decompose strings.

    >>> list(flatten([1, [2, 3, (4, 5)], 6]))
    [1, 2, 3, 4, 5, 6]
    >>> list(flatten('hello'))
    ['hello']
    >>> list(flatten(['hello', ['world'], [], []]))
    ['hello', 'world']

    @param value: any object
    @type value: `object`
    @return: a 'flat' iterator on the elements of `value` and its
        nested iterable objects (except strings)
    @rtype: `generator`
    """
    if isinstance(value, (str, bytes)) :
        yield value
    else :
        try :
            for item in value :
                for child in flatten(item) :
                    yield child
        except TypeError :
            yield value

@hashable
class mset (Counter) :
    def _hash_items (self) :
        return self.items()
    __delitem__ = mutation(Counter.__delitem__)
    __setitem__ = mutation(Counter.__setitem__)
    clear = mutation(Counter.clear)
    pop = mutation(Counter.pop)
    popitem = mutation(Counter.popitem)
    setdefault = mutation(Counter.setdefault)
    update = mutation(Counter.update)
    def __call__ (self, value) :
        return Counter.__getitem__(self, value)
    def __getitem__ (self, value) :
        if value in self :
            return Counter.__getitem__(self, value)
        else :
            raise KeyError(value)
    def __sub__ (self, other) :
        if not other <= self :
            raise ValueError("not enough occurrences")
        return Counter.__sub__(self, other)
    def __str__ (self) :
        elt = []
        for val, num in Counter.items(self) :
            if num == 1 :
                elt.append(str(val))
            else :
                elt.append("%s(*%s)" % (val, num))
        return "{%s}" % ", ".join(elt)
    @mutation
    def __setitem__ (self, key, value) :
        if value < 0 :
            raise ValueError("negative count forbidden")
        elif value == 0 :
            if key in self :
                del self[key]
        else :
            Counter.__setitem__(self, key, value)
    @mutation
    def add (self, values, times=1) :
        self.update(list(iterate(values)) * times)
    @mutation
    def __iadd__ (self, values) :
        self.add(values)
        return self
    @mutation
    def sub (self, values, times=1) :
        self.subtract(list(iterate(values)) * times)
    @mutation
    def __isub__ (self, values) :
        self.sub(values)
        return self
    @mutation
    def remove (self, values, times=1) :
        new = self - self.__class__(list(iterate(values)) * times)
        self.clear()
        self.update(new)
    def __iter__ (self) :
        for key, val in Counter.items(self) :
            for i in range(val) :
                yield key
    def items (self) :
        return self.__iter__()
    def domain (self) :
        return set(self.keys())
    def pairs (self) :
        return Counter.items(self)
    def __len__ (self) :
        return sum(self.values(), 0)
    def size (self) :
        return Counter.__len__(self)
    def __mul__ (self, num) :
        """Multiplication by a non-negative integer.

        >>> mset('abc') * 3 == mset('abc' * 3)
        True
        >>> mset('abc') * 0 == mset()
        True
        """
        if num == 0 :
            return self.__class__()
        new = self.copy()
        new.__imul__(num)
        return new
    @mutation
    def __imul__ (self, num) :
        """In-place multiplication by a non-negative integer.

        >>> m = mset('abc')
        >>> m *= 3
        >>> m == mset('abc' * 3)
        True
        >>> m *= 0
        >>> m == mset()
        True
        """
        if num == 0 :
            self.clear()
        else :
            for key, val in Counter.items(self) :
                self[key] = val * num
        return self
    def __le__ (self, other) :
        """Test for inclusion.

        >>> mset([1, 2, 3]) <= mset([1, 2, 3, 4])
        True
        >>> mset([1, 2, 3]) <= mset([1, 2, 3, 3])
        True
        >>> mset([1, 2, 3]) <= mset([1, 2, 3])
        True
        >>> mset([1, 2, 3]) <= mset([1, 2])
        False
        >>> mset([1, 2, 2]) <= mset([1, 2, 3, 4])
        False
        """
        return all(self(k) <= other(k) for k in self.keys())
    def __lt__ (self, other) :
        """Test for strict inclusion. A multiset `A` is strictly
        included in a multiset `B` iff every element in `A` is also in
        `B` but less repetitions `A` than in `B`.

        >>> mset([1, 2, 3]) < mset([1, 2, 3, 4])
        True
        >>> mset([1, 2, 3]) < mset([1, 2, 3, 3])
        True
        >>> mset([1, 2, 3]) < mset([1, 2, 3])
        False
        >>> mset([1, 2, 3]) < mset([1, 2])
        False
        >>> mset([1, 2, 2]) < mset([1, 2, 3, 4])
        False
        """
        return (self != other) and (self <= other)
    def __ge__ (self, other) :
        """Test for inclusion.

        >>> mset([1, 2, 3, 4]) >= mset([1, 2, 3])
        True
        >>> mset([1, 2, 3, 3]) >= mset([1, 2, 3])
        True
        >>> mset([1, 2, 3]) >= mset([1, 2, 3])
        True
        >>> mset([1, 2]) >= mset([1, 2, 3])
        False
        >>> mset([1, 2, 3, 4]) >= mset([1, 2, 2])
        False
        """
        return all(self(k) >= other(k) for k in other.keys())
    def __gt__ (self, other) :
        """Test for strict inclusion.

        >>> mset([1, 2, 3, 4]) > mset([1, 2, 3])
        True
        >>> mset([1, 2, 3, 3]) > mset([1, 2, 3])
        True
        >>> mset([1, 2, 3]) > mset([1, 2, 3])
        False
        >>> mset([1, 2]) > mset([1, 2, 3])
        False
        >>> mset([1, 2, 3, 4]) > mset([1, 2, 2])
        False
        """
        return (self != other) and (self >= other)

class WordSet (set) :
    """A set of words being able to generate fresh words.
    """
    def copy (self) :
        return self.__class__(self)
    def fresh (self, add=False, min=1, base="",
               allowed="abcdefghijklmnopqrstuvwxyz") :
        """Create a fresh word (ie, which is not in the set).

        >>> w = WordSet(['foo', 'bar'])
        >>> list(sorted(w))
        ['bar', 'foo']
        >>> w.fresh(True, 3)
        'aaa'
        >>> list(sorted(w))
        ['aaa', 'bar', 'foo']
        >>> w.fresh(True, 3)
        'baa'
        >>> list(sorted(w))
        ['aaa', 'baa', 'bar', 'foo']

        @param add: add the created word to the set if `add=True`
        @type add: `bool`
        @param min: minimal length of the new word
        @type min: `int`
        @param allowed: characters allowed in the new word
        @type allowed: `str`
        @param base: prefix of generated words
        @type base: `str`
        """
        if base :
            result = [base] + [allowed[0]] * max(0, min - len(base))
            if base in self :
                result.append(allowed[0])
                pos = len(result) - 1
            elif len(base) < min :
                pos = 1
            else :
                pos = 0
        else :
            result = [allowed[0]] * min
            pos = 0
        while "".join(result) in self :
            for c in allowed :
                try :
                    result[pos] = c
                except IndexError :
                    result.append(c)
                if "".join(result) not in self :
                    break
            pos += 1
        if add :
            self.add("".join(result))
        return "".join(result)
