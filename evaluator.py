from __future__ import division
from pyparsing import (Literal, CaselessLiteral, Word, Combine, Group, Optional,
                       ZeroOrMore, Forward, nums, alphas, oneOf)
import math
import operator
import utils


class NumericStringParser(object):

    def pushFirst(self, strg, loc, toks):
        self.exprStack.append(toks[0])

    def pushUMinus(self, strg, loc, toks):
        if toks and toks[0] == '-':
            self.exprStack.append('unary -')

    def __init__(self):
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
                 (ident + lpar + expr + rpar | pi | e | fnumber).setParseAction(self.pushFirst))
                | Optional(oneOf("- +")) + Group(lpar + expr + rpar)
                ).setParseAction(self.pushUMinus)

        factor = Forward()
        factor << atom + \
            ZeroOrMore((expop + factor).setParseAction(self.pushFirst))
        term = factor + \
            ZeroOrMore((multop + factor).setParseAction(self.pushFirst))
        expr << term + \
            ZeroOrMore((addop + term).setParseAction(self.pushFirst))
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

    def evaluateStack(self, s):
        op = s.pop()
        if op == 'unary -':
            op2 = self.evaluateStack(s)
            return lambda v: -op2(v)
        if op in "+-*/^":
            op2 = self.evaluateStack(s)
            op1 = self.evaluateStack(s)
            return lambda v: utils.none_filter(self.opn[op])(op1(v), op2(v))
        elif op == "PI":
            return lambda v: math.pi
        elif op == "E":
            return lambda v: math.e
        elif op in self.fn:
            op2 = self.evaluateStack(s)
            return lambda v: utils.none_filter(self.fn[op])(op2(v))
        elif op[0] == "~":
            return lambda v: v[int(op[1:])]
        else:
            return lambda v: float(op)

    def compile(self, num_string, parseAll=True):
        self.exprStack = []
        self.bnf.parseString(num_string, parseAll)
        return self.evaluateStack(self.exprStack)
