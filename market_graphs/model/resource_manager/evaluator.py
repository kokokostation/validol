import numpy as np
import operator
import math

import pyparsing as pp


class Atom:
    def __init__(self, name, letter=None):
        self.name = name
        self.letter = letter

    @property
    def independent(self):
        return self.letter is None

    @property
    def full_name(self):
        if self.independent:
            return self.name
        else:
            return "{name}({letter})".format(name=self.name, letter=self.letter)


class NumericStringParser:
    def push_first(self, toks):
        self.expr_stack.append(toks[0])

    def push_uminus(self, toks):
        if toks and toks[0] == '-':
            self.expr_stack.append('unary -')

    def atom_from_toks(self, toks):
        if self.atom is not None:
            return Atom(toks[0], self.atom.letter)
        else:
            return Atom(*toks)

    @staticmethod
    def atom_or(atoms):
        return pp.Or(map(pp.Literal,
                         sorted([atom.name for atom in atoms], key=lambda x: -len(x))))

    def __init__(self, evaluator):
        self.evaluator = evaluator
        self.expr_stack = []
        self.atom = None

        point = pp.Literal(".")
        e = pp.CaselessLiteral("E")
        lpar = pp.Literal("(").suppress()
        rpar = pp.Literal(")").suppress()

        independent_atom = NumericStringParser.atom_or(self.evaluator.independent_atoms)\
            .setParseAction(lambda toks: Atom(toks[0]))

        dependent_atom = (NumericStringParser.atom_or(self.evaluator.dependent_atoms) +
                          pp.Optional(lpar + pp.Word(pp.alphas, exact=1) + rpar)) \
            .setParseAction(self.atom_from_toks)

        fnumber = dependent_atom | independent_atom | pp.Combine(pp.Word("+-" + pp.nums, pp.nums) +
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

    def evaluate_stack(self, stack):
        op = stack.pop()

        if isinstance(op, Atom):
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

    def evaluate_atom(self, atom):
        self.atom = atom

        return self.evaluate(self.evaluator.atoms_map[atom.name].formula)

    def evaluate(self, formula):
        self.bnf.parseString(formula, True)
        return self.evaluate_stack(self.expr_stack)


class Evaluator:
    def __init__(self, df, all_atoms):
        self.df = df
        self.independent_atoms = [atom for atom in all_atoms if atom.independent]
        self.dependent_atoms = [atom for atom in all_atoms if not atom.independent]
        self.atoms_map = {atom.name: atom for atom in all_atoms}

    def evaluate_atom(self, atom):
        if atom.full_name not in self.df:
            self.df[atom.full_name] = NumericStringParser(self).evaluate_atom(atom)

        return self.df[atom.full_name]

    def evaluate(self, formulas):
        for formula in formulas:
            self.df[formula] = NumericStringParser(self).evaluate(formula)

    def get_result(self):
        return self.df