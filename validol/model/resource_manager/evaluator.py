import numpy as np
import operator
import math
import re

import pyparsing as pp

from validol.model.resource_manager.atom_base import AtomBase


class AtomRepr(AtomBase):
    def __init__(self, name, params, params_map=None):
        params = params if params_map is None else [params_map.get(x, x) for x in params]
        AtomBase.__init__(self, name, params)


class FormulaGrammar:
    def push_first(self, toks):
        self.expr_stack.append(toks[0])

    def push_uminus(self, toks):
        if toks and toks[0] == '-':
            self.expr_stack.append('unary -')

    def __init__(self, all_atoms):
        self.expr_stack = []
        self.params_map = None

        point = pp.Literal(".")
        e = pp.CaselessLiteral("E")
        lpar = pp.Literal("(").suppress()
        rpar = pp.Literal(")").suppress()

        atom_names = [atom.name for atom in all_atoms]
        chars = re.sub('[,()]', "", pp.printables)
        validol_atom = pp.Or([
            pp.Literal(atom_name) + lpar + pp.Group(pp.delimitedList(pp.Word(chars))) + rpar
            for atom_name in sorted(atom_names, key=lambda x: -len(x))]).setParseAction(
            lambda toks: AtomRepr(toks[0], toks[1], self.params_map)
        )

        fnumber = validol_atom | pp.Combine(pp.Word("+-" + pp.nums, pp.nums) +
                             pp.Optional(point + pp.Optional(pp.Word(pp.nums))) +
                             pp.Optional(e + pp.Word("+-" + pp.nums, pp.nums)))
        ident = pp.Word(pp.alphas, pp.alphas + pp.nums + "_$")
        plus = pp.Literal("+")
        minus = pp.Literal("-")
        mult = pp.Literal("*")
        div = pp.Literal("/")
        addop = plus | minus
        multop = mult | div
        expop = pp.Literal("^")
        pi = pp.CaselessLiteral("PI")
        expr = pp.Forward()
        atom = ((pp.Optional(pp.oneOf("- +")) +
                 (ident + lpar + expr + rpar | pi | e | fnumber).setParseAction(self.push_first))
                | pp.Optional(pp.oneOf("- +")) + pp.Group(lpar + expr + rpar)) \
            .setParseAction(self.push_uminus)

        factor = pp.Forward()
        factor << atom + pp.ZeroOrMore((expop + factor).setParseAction(self.push_first))
        term = factor + pp.ZeroOrMore((multop + factor).setParseAction(self.push_first))
        expr << term + pp.ZeroOrMore((addop + term).setParseAction(self.push_first))

        self.bnf = expr

        self.opn = {"+": operator.add,
                    "-": operator.sub,
                    "*": operator.mul,
                    "/": operator.truediv,
                    "^": operator.pow}
        self.fn = {"sin": np.sin,
                   "cos": np.cos,
                   "tan": np.tan,
                   "exp": np.exp,
                   "abs": np.abs,
                   "round": np.round}


class NumericStringParser(FormulaGrammar):
    def __init__(self, evaluator):
        FormulaGrammar.__init__(self, evaluator.atoms_map.values())

        self.evaluator = evaluator

    def evaluate_stack(self, stack):
        op = stack.pop()

        if isinstance(op, AtomRepr):
            return self.evaluator.evaluate_atom(op)
        elif op == 'unary -':
            return -self.evaluate_stack(stack)
        elif op in "+-*/^":
            op2 = self.evaluate_stack(stack)
            op1 = self.evaluate_stack(stack)
            return self.opn[op](op1, op2)
        elif op == "PI":
            return math.pi
        elif op == "E":
            return math.e
        elif op in self.fn:
            return self.fn[op](self.evaluate_stack(stack))
        else:
            return float(op)

    def evaluate(self, formula, params_map=None):
        self.expr_stack = []
        self.params_map = params_map

        self.bnf.parseString(formula, True)

        return self.evaluate_stack(self.expr_stack)


class Evaluator:
    def __init__(self, model_launcher, df, letter_map):
        self.model_launcher = model_launcher
        self.df = df
        self.letter_map = letter_map
        self.atoms_map = {atom.name: atom for atom in self.model_launcher.get_atoms()}
        self.parser = NumericStringParser(self)

    def evaluate_atom(self, atom):
        if str(atom) not in self.df:
            self.atoms_map[atom.name].evaluate(self, atom.params, str(atom))

        return self.df[str(atom)]

    def evaluate(self, formulas):
        for formula in formulas:
            self.df[formula] = self.parser.evaluate(formula)

    def get_result(self):
        return self.df

    @staticmethod
    def merge_dfs(dfa, dfb):
        return dfa.merge(dfb, 'outer', 'Date', sort=True)