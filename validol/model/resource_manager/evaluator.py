import numpy as np
import operator
import pandas as pd
import pyparsing as pp

from validol.model.utils.utils import merge_dfs, FillSeries
from validol.model.store.structures.structure import PieceNameError
from validol.model.resource_manager.data import Data


class AtomWrap:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name


VAR = pp.Word('@', pp.alphas)
STRING = pp.Word(pp.alphas + '%_' + pp.nums)
MATH_FUNCTIONS = {
    "sin": np.sin,
    "cos": np.cos,
    "tan": np.tan,
    "exp": np.exp,
    "abs": np.abs,
    "round": np.round
}
ARITHMETIC_OPERATIONS = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
    "^": operator.pow
}


class FormulaGrammar:
    def push_first(self, toks):
        self.expr_stack.append(toks[0])

    def args_num(self, toks):
        self.expr_stack.append(len(toks))

    def push_uminus(self, toks):
        if toks and toks[0] == '-':
            self.expr_stack.append('unary -')

    def __init__(self, all_atoms, var=VAR):
        self.expr_stack = []

        point = pp.Literal(".")
        lpar = pp.Literal("(")
        rpar = pp.Literal(")")

        expr = pp.Forward()

        validol_atom = pp.Or([pp.Literal(atom_name) for atom_name in
                              sorted(all_atoms, key=lambda x: -len(x))]).setParseAction(lambda toks: AtomWrap(toks[0]))

        fnumber = pp.Combine(pp.Word("+-" + pp.nums, pp.nums) +
                             pp.Optional(point + pp.Optional(pp.Word(pp.nums))))\
            .setParseAction(lambda toks: [float(toks[0])])

        ident = pp.Word(pp.alphas, pp.alphas + pp.nums + "_$")

        args = lpar + (pp.Optional(pp.Combine(expr)) + pp.ZeroOrMore(pp.Combine(pp.Literal(',') + expr)))\
            .setParseAction(self.args_num) + rpar

        function = (validol_atom + args)
        st_function = ident + args

        date = pp.Combine(pp.Word(pp.nums, exact=4) + (pp.Literal('-') + pp.Word(pp.nums, exact=2)) * 2)
        none = pp.CaselessLiteral('None').setParseAction(lambda toks: [None])

        plus = pp.Literal("+")
        minus = pp.Literal("-")
        mult = pp.Literal("*")
        div = pp.Literal("/")
        addop = plus | minus
        multop = mult | div
        expop = pp.Literal("^")
        true_atom = (function | st_function | date | fnumber | var | none | STRING)\
            .setParseAction(self.push_first)
        atom = ((pp.Optional(pp.oneOf("- +")) + true_atom) |
                pp.Optional(pp.oneOf("- +")) + pp.Group(lpar + expr + rpar))\
            .setParseAction(self.push_uminus)

        factor = pp.Forward()
        factor << atom + pp.ZeroOrMore((expop + factor).setParseAction(self.push_first))
        term = factor + pp.ZeroOrMore((multop + factor).setParseAction(self.push_first))
        expr << term + pp.ZeroOrMore((addop + term).setParseAction(self.push_first))

        self.bnf = expr


class AtomGrammar:
    def __init__(self, all_atoms):
        self.all_atoms = [atom.name for atom in all_atoms]

        lpar = pp.Literal("(").suppress()
        rpar = pp.Literal(")").suppress()

        self.bnf = STRING.setResultsName('name') + \
                   lpar + pp.Optional(pp.delimitedList(VAR)).setResultsName('vars') + rpar

    def parse(self, atom, named_formula):
        result = self.bnf.parseString(atom)
        result = {'name': result['name'], 'vars': list(result.get('vars', []))}

        if result['name'] in self.all_atoms:
            raise PieceNameError

        FormulaGrammar(self.all_atoms, pp.Or([pp.Literal(var) for var in result['vars']]))\
            .bnf.parseString(named_formula, True)

        return result


class NumericStringParser(FormulaGrammar):
    def __init__(self, evaluator):
        FormulaGrammar.__init__(self, evaluator.atoms_map.keys())

        self.evaluator = evaluator
        self.cache = {}

    def evaluate_stack(self, stack, params_map):
        op = stack.pop()

        if isinstance(op, float) or op is None:
            return self.evaluator.evaluate_numeric(op)
        elif isinstance(op, AtomWrap):
            atom = self.evaluator.atoms_map[op.name]
            args_num = stack.pop()
            params = list(reversed([self.evaluate_stack(stack, params_map) for _ in range(args_num)]))

            name = atom.cache_name(params)

            if name not in self.cache:
                result = self.evaluator.evaluate_atom(atom, params)

                if name is not None:
                    self.cache[name] = result
            else:
                result = self.cache[name]

            if atom.note() is not None:
                return result, atom.note()
            else:
                return result
        elif op[0] == '@':
            return self.evaluator.evaluate_var(op, params_map)
        elif op == 'unary -':
            return self.evaluator.evaluate_unary_minus(self.evaluate_stack(stack, params_map))
        elif op in ARITHMETIC_OPERATIONS:
            operands = [self.evaluate_stack(stack, params_map) for _ in range(2)]

            return self.evaluator.evaluate_arithmetic(op, operands)
        elif op in MATH_FUNCTIONS:
            stack.pop()

            return self.evaluator.evaluate_math_function(op, self.evaluate_stack(stack, params_map))
        else:
            return self.evaluator.evaluate_other(op)

    def evaluate(self, formula, params_map=None):
        self.bnf.parseString(formula, True)

        return self.evaluate_stack(self.expr_stack, params_map)


class BaseEvaluator:
    def __init__(self, model_launcher):
        self.model_launcher = model_launcher
        self.atoms_map = {atom.name: atom for atom in model_launcher.get_atoms()}
        self.parser = NumericStringParser(self)

    def evaluate_numeric(self, data):
        raise NotImplementedError()

    def evaluate_atom(self, atom, params):
        raise NotImplementedError()

    def evaluate_var(self, data, params_map):
        raise NotImplementedError()

    def evaluate_unary_minus(self, data):
        raise NotImplementedError()

    def evaluate_arithmetic(self, op, operands):
        raise NotImplementedError()

    def evaluate_math_function(self, op, operand):
        raise NotImplementedError()

    def evaluate_other(self, data):
        raise NotImplementedError()

    def evaluate(self, formulas):
        raise NotImplementedError()


class Evaluator(BaseEvaluator):
    def __init__(self, model_launcher, df, letter_map, range_):
        super(Evaluator, self).__init__(model_launcher)

        self.df = df
        self.letter_map = letter_map
        self.range = range_

    def evaluate_numeric(self, data):
        return data

    def evaluate_atom(self, atom, params):
        return atom.evaluate(self, params)

    def evaluate_var(self, data, params_map):
        return params_map[data]

    def evaluate_unary_minus(self, data):
        return -data

    def evaluate_arithmetic(self, op, operands):
        for i, operand in enumerate(operands):
            if isinstance(operand, FillSeries):
                operands[i] = operand.adjust(operands[1 - i])

        return ARITHMETIC_OPERATIONS[op](*reversed(operands))

    def evaluate_math_function(self, op, operand):
        return MATH_FUNCTIONS[op](operand)

    def evaluate_other(self, data):
        return data

    def evaluate(self, formulas):
        df = pd.DataFrame()
        info = {}

        for formula in formulas:
            result = self.parser.evaluate(formula)

            if isinstance(result, tuple):
                info[formula] = result[1]
                result = result[0]

            if isinstance(result, pd.Series):
                df = merge_dfs(df, result.to_frame(formula))
            else:
                df[formula] = result

        df.dropna(axis=0, how='all', inplace=True)

        return Data(df, info)


class DependenciesEvaluator(BaseEvaluator):
    def __init__(self, model_launcher):
        super().__init__(model_launcher)

    def evaluate_numeric(self, data):
        return set()

    def evaluate_atom(self, atom, params):
        return atom.list_dependencies(self, params)

    def evaluate_var(self, data, params_map):
        return params_map[data]

    def evaluate_unary_minus(self, data):
        return data

    def evaluate_arithmetic(self, op, operands):
        return set().union(*operands)

    def evaluate_math_function(self, op, operand):
        return operand

    def evaluate_other(self, data):
        return data

    def evaluate(self, formulas, params_map=None):
        deps_list = []
        for formula in formulas:
            result = self.parser.evaluate(formula, params_map)
            if isinstance(result, tuple):
                deps = result[0]
            else:
                deps = result

            deps_list.append(deps)

        return deps_list


class SerializingEvaluator(BaseEvaluator):
    def __init__(self, model_launcher):
        super().__init__(model_launcher)

    def evaluate_numeric(self, data):
        return str(data)

    def evaluate_atom(self, atom, params):
        return atom.serialize(self, params)

    def evaluate_var(self, data, params_map):
        return str(params_map[data])

    def evaluate_unary_minus(self, data):
        return f'-{data}'

    def evaluate_arithmetic(self, op, operands):
        return f'({operands[0]} {op} {operands[1]})'

    def evaluate_math_function(self, op, operand):
        return f'{op}({operand})'

    def evaluate_other(self, data):
        return str(data)

    def evaluate(self, formulas, params_map=None):
        deps_list = []
        for formula in formulas:
            result = self.parser.evaluate(formula, params_map)
            if isinstance(result, tuple):
                deps = result[0]
            else:
                deps = result

            deps_list.append(deps)

        return deps_list
