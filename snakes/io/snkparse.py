#!/usr/bin/env python
# -*- coding: utf-8 -*-

# CAVEAT UTILITOR
#
# This file was automatically generated by TatSu.
#
#    https://pypi.python.org/pypi/tatsu/
#
# Any changes you make to it will be overwritten the next time
# the file is generated.


from __future__ import print_function, division, absolute_import, unicode_literals

from tatsu.buffering import Buffer
from tatsu.parsing import Parser
from tatsu.parsing import tatsumasu
from tatsu.util import re, generic_main  # noqa


KEYWORDS = {}  # type: ignore


class snkBuffer(Buffer):
    def __init__(
        self,
        text,
        whitespace=re.compile('[\\t ]+'),
        nameguard=None,
        comments_re=None,
        eol_comments_re='#.*?$',
        ignorecase=None,
        namechars='',
        **kwargs
    ):
        super(snkBuffer, self).__init__(
            text,
            whitespace=whitespace,
            nameguard=nameguard,
            comments_re=comments_re,
            eol_comments_re=eol_comments_re,
            ignorecase=ignorecase,
            namechars=namechars,
            **kwargs
        )


class snkParser(Parser):
    def __init__(
        self,
        whitespace=re.compile('[\\t ]+'),
        nameguard=None,
        comments_re=None,
        eol_comments_re='#.*?$',
        ignorecase=None,
        left_recursion=True,
        parseinfo=True,
        keywords=None,
        namechars='',
        buffer_class=snkBuffer,
        **kwargs
    ):
        if keywords is None:
            keywords = KEYWORDS
        super(snkParser, self).__init__(
            whitespace=whitespace,
            nameguard=nameguard,
            comments_re=comments_re,
            eol_comments_re=eol_comments_re,
            ignorecase=ignorecase,
            left_recursion=left_recursion,
            parseinfo=parseinfo,
            keywords=keywords,
            namechars=namechars,
            buffer_class=buffer_class,
            **kwargs
        )

    @tatsumasu()
    def _spec_(self):  # noqa
        with self._optional():
            self._nl_()
        self._token('lang')
        self._text_()
        self.name_last_node('lang')
        self._nl_()

        def block2():
            self._decl_()
        self._closure(block2)
        self.name_last_node('declare')
        self._token('net')
        self._text_()
        self.name_last_node('net')
        self._token(':')
        self._nl_()

        def block5():
            with self._choice():
                with self._option():
                    self._trans_()
                with self._option():
                    self._place_()
                self._error('no available options')
        self._positive_closure(block5)
        self.name_last_node('nodes')
        with self._optional():
            self._nl_()
        self._check_eof()
        self.ast._define(
            ['declare', 'lang', 'net', 'nodes'],
            []
        )

    @tatsumasu()
    def _decl_(self):  # noqa
        with self._optional():
            self._nl_()
        self._token('declare')
        self._text_()
        self.name_last_node('source')
        self._nl_()
        self.ast._define(
            ['source'],
            []
        )

    @tatsumasu()
    def _place_(self):  # noqa
        with self._optional():
            self._nl_()
        self._token('place')
        self._text_()
        self.name_last_node('name')
        with self._optional():
            self._text_()
            self.name_last_node('type')
        with self._optional():
            self._token('=')
            with self._group():

                def sep3():
                    self._token(',')

                def block3():
                    self._token_()
                self._positive_join(block3, sep3)
            self.name_last_node('tokens')
        self._nl_()
        self.ast._define(
            ['name', 'tokens', 'type'],
            []
        )

    @tatsumasu()
    def _token_(self):  # noqa
        with self._choice():
            with self._option():
                self._number_()
                self.name_last_node('number')
            with self._option():
                self._text_()
                self.name_last_node('text')
            self._error('no available options')
        self.ast._define(
            ['number', 'text'],
            []
        )

    @tatsumasu()
    def _trans_(self):  # noqa
        with self._optional():
            self._nl_()
        self._token('trans')
        self._text_()
        self.name_last_node('name')
        with self._optional():
            self._pattern(r'[^:]+')
            self.name_last_node('guard')
        self._token(':')
        self._nl_()

        def block3():
            self._arc_()
        self._positive_closure(block3)
        self.name_last_node('arcs')
        self.ast._define(
            ['arcs', 'guard', 'name'],
            []
        )

    @tatsumasu()
    def _arc_(self):  # noqa
        with self._optional():
            self._nl_()
        with self._group():
            with self._choice():
                with self._option():
                    self._token('<')
                with self._option():
                    self._token('>')
                self._error('no available options')
        self.name_last_node('way')
        self._text_()
        self.name_last_node('place')
        with self._optional():
            self._arcmod_()
            self.name_last_node('mod')
        self._arckind_()
        self.name_last_node('kind')
        self._token('=')
        self._tail_()
        self.name_last_node('label')
        self._nl_()
        self.ast._define(
            ['kind', 'label', 'mod', 'place', 'way'],
            []
        )

    @tatsumasu()
    def _arckind_(self):  # noqa
        with self._choice():
            with self._option():
                self._token('val')
            with self._option():
                self._token('var')
            with self._option():
                self._token('expr')
            with self._option():
                self._token('tuple')
            with self._option():
                self._token('flush')
            with self._option():
                self._token('fill')
            self._error('no available options')

    @tatsumasu()
    def _arcmod_(self):  # noqa
        with self._choice():
            with self._option():
                self._token('?')
                self.name_last_node('kind')
            with self._option():
                self._token('!')
                self.name_last_node('kind')
                with self._optional():
                    self._code_()
                    self.name_last_node('guard')
            self._error('no available options')
        self.ast._define(
            ['guard', 'kind'],
            []
        )

    @tatsumasu()
    def _tuple_(self):  # noqa
        self._token('(')

        def sep0():
            self._token(',')

        def block0():
            with self._choice():
                with self._option():
                    self._tuple_()
                with self._option():
                    self._text_()
                with self._option():
                    self._number_()
                self._error('no available options')
        self._positive_join(block0, sep0)
        self._token(')')

    @tatsumasu()
    def _tail_(self):  # noqa
        self._pattern(r'.*?$')

    @tatsumasu()
    def _number_(self):  # noqa
        self._pattern(r'[+-]?[0-9]+')

    @tatsumasu()
    def _nl_(self):  # noqa
        self._pattern(r'\s*[\n\r]\s*')

    @tatsumasu()
    def _text_(self):  # noqa
        with self._choice():
            with self._option():
                self._code_()
                self.name_last_node('code')
            with self._option():
                self._name_()
                self.name_last_node('name')
            with self._option():
                self._string_()
                self.name_last_node('string')
            self._error('no available options')
        self.ast._define(
            ['code', 'name', 'string'],
            []
        )

    @tatsumasu()
    def _code_(self):  # noqa
        with self._choice():
            with self._option():
                self._token('{')
                self._TEXTC_()
                self._token('}')
            with self._option():
                self._token('(')
                self._TEXTP_()
                self._token(')')
            with self._option():
                self._token('[')
                self._TEXTB_()
                self._token(']')
            self._error('no available options')

    @tatsumasu()
    def _TEXTC_(self):  # noqa

        def block0():
            with self._choice():
                with self._option():
                    self._pattern(r'([^{}]|\\[{}])*')
                with self._option():
                    self._TEXTC_()
                self._error('no available options')
        self._closure(block0)

    @tatsumasu()
    def _TEXTP_(self):  # noqa

        def block0():
            with self._choice():
                with self._option():
                    self._pattern(r'([^()]|\\[()])*')
                with self._option():
                    self._TEXTP_()
                self._error('no available options')
        self._closure(block0)

    @tatsumasu()
    def _TEXTB_(self):  # noqa

        def block0():
            with self._choice():
                with self._option():
                    self._pattern(r'([^\[\]]|\\[\[\]])*')
                with self._option():
                    self._TEXTB_()
                self._error('no available options')
        self._closure(block0)

    @tatsumasu()
    def _name_(self):  # noqa
        self._pattern(r'[a-zA-Z_][a-zA-Z0-9_]*')

    @tatsumasu()
    def _string_(self):  # noqa
        with self._choice():
            with self._option():
                self._token("'''")

                def block0():
                    with self._choice():
                        with self._option():
                            self._pattern(r"[^'\\]+")
                        with self._option():
                            self._token("''")
                            with self._ifnot():
                                self._token("'")
                        with self._option():
                            self._token("'")
                            with self._ifnot():
                                self._token("'")
                        with self._option():
                            self._pattern(r'\\(.|\n)')
                        self._error('no available options')
                self._closure(block0)
                self._token("'''")
            with self._option():
                self._token('"""')

                def block2():
                    with self._choice():
                        with self._option():
                            self._pattern(r'[^"\\]+')
                        with self._option():
                            self._token('""')
                            with self._ifnot():
                                self._token('"')
                        with self._option():
                            self._token('"')
                            with self._ifnot():
                                self._token('"')
                        with self._option():
                            self._pattern(r'\\(.|\n)')
                        self._error('no available options')
                self._closure(block2)
                self._token('"""')
            with self._option():
                self._token("'")

                def block4():
                    with self._choice():
                        with self._option():
                            self._token('\\')
                            self._pattern(r'.')
                        with self._option():
                            self._pattern(r"[^\\\r\n\f']+")
                        self._error('no available options')
                self._closure(block4)
                self._token("'")
            with self._option():
                self._token('"')

                def block6():
                    with self._choice():
                        with self._option():
                            self._token('\\')
                            self._pattern(r'.')
                        with self._option():
                            self._pattern(r'[^\\\r\n\f"]+')
                        self._error('no available options')
                self._closure(block6)
                self._token('"')
            self._error('no available options')


class snkSemantics(object):
    def spec(self, ast):  # noqa
        return ast

    def decl(self, ast):  # noqa
        return ast

    def place(self, ast):  # noqa
        return ast

    def token(self, ast):  # noqa
        return ast

    def trans(self, ast):  # noqa
        return ast

    def arc(self, ast):  # noqa
        return ast

    def arckind(self, ast):  # noqa
        return ast

    def arcmod(self, ast):  # noqa
        return ast

    def tuple(self, ast):  # noqa
        return ast

    def tail(self, ast):  # noqa
        return ast

    def number(self, ast):  # noqa
        return ast

    def nl(self, ast):  # noqa
        return ast

    def text(self, ast):  # noqa
        return ast

    def code(self, ast):  # noqa
        return ast

    def TEXTC(self, ast):  # noqa
        return ast

    def TEXTP(self, ast):  # noqa
        return ast

    def TEXTB(self, ast):  # noqa
        return ast

    def name(self, ast):  # noqa
        return ast

    def string(self, ast):  # noqa
        return ast


def main(filename, startrule, **kwargs):
    with open(filename) as f:
        text = f.read()
    parser = snkParser()
    return parser.parse(text, startrule, filename=filename, **kwargs)


if __name__ == '__main__':
    import json
    from tatsu.util import asjson

    ast = generic_main(main, snkParser, name='snk')
    print('AST:')
    print(ast)
    print()
    print('JSON:')
    print(json.dumps(asjson(ast), indent=2))
    print()