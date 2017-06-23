from __future__ import division

import math
import operator

from pyparsing import (Literal, CaselessLiteral, Word, Combine, Group, Optional,
                       ZeroOrMore, Forward, nums, alphas, oneOf)

from model import utils


class NumericStringParser():
    def push_first(self, strg, loc, toks):
        self.expr_stack.append(toks[0])

    def push_uminus(self, strg, loc, toks):
        if toks and toks[0] == '-':
            self.expr_stack.append('unary -')

    def __init__(self):
        self.expr_stack = []

        point = Literal(".")
        e = CaselessLiteral("E")
        fnumber = Combine(Word("+-" + nums, nums) +
                          Optional(point + Optional(Word(nums))) +
                          Optional(e + Word("+-" + nums, nums))) | Word("~" + nums)
        ident = Word(alphas, alphas + nums + "_$")
        plus = Literal("+")
        minus = Literal("-")
        mult = Literal("*")
        div = Literal("/")
        lpar = Literal("(").suppress()
        rpar = Literal(")").suppress()
        addop = plus | minus
        multop = mult | div
        expop = Literal("^")
        pi = CaselessLiteral("PI")
        expr = Forward()
        atom = ((Optional(oneOf("- +")) +
                 (ident + lpar + expr + rpar | pi | e | fnumber).setParseAction(self.push_first))
                | Optional(oneOf("- +")) + Group(lpar + expr + rpar)
                ).setParseAction(self.push_uminus)

        factor = Forward()
        factor << atom + \
            ZeroOrMore((expop + factor).setParseAction(self.push_first))
        term = factor + \
            ZeroOrMore((multop + factor).setParseAction(self.push_first))
        expr << term + \
            ZeroOrMore((addop + term).setParseAction(self.push_first))
        self.bnf = expr

        self.opn = {"+": operator.add,
                    "-": operator.sub,
                    "*": operator.mul,
                    "/": utils.my_division,
                    "^": operator.pow}
        self.fn = {"sin": math.sin,
                   "cos": math.cos,
                   "tan": math.tan,
                   "exp": math.exp,
                   "abs": abs,
                   "trunc": lambda a: int(a),
                   "round": round}

    def evaluate_stack(self, s):
        op = s.pop()

        if op == 'unary -':
            op2 = self.evaluate_stack(s)
            return lambda v: -op2(v)
        if op in "+-*/^":
            op2 = self.evaluate_stack(s)
            op1 = self.evaluate_stack(s)
            return lambda v: utils.none_filter(self.opn[op])(op1(v), op2(v))
        elif op == "PI":
            return lambda v: math.pi
        elif op == "E":
            return lambda v: math.e
        elif op in self.fn:
            op2 = self.evaluate_stack(s)
            return lambda v: utils.none_filter(self.fn[op])(op2(v))
        elif op[0] == "~":
            return lambda v: v[int(op[1:])]
        else:
            return lambda v: float(op)

    def compile(self, num_string, parseAll=True):
        self.expr_stack = []
        self.bnf.parseString(num_string, parseAll)
        return self.evaluate_stack(self.expr_stack)
