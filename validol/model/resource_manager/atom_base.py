from functools import wraps

from validol.model.utils import parse_isoformat_date

class AtomBase:
    def __init__(self, name, params):
        self.name = name
        self.params = params

    def cache_name(self, params):
        if all(any(isinstance(param, typ) for typ in (str, float)) for param in params):
            return str(AtomBase(self.name, params))
        else:
            return None

    def __str__(self):
        return "{name}({params})".format(name=self.name, params=', '.join(map(str, self.params)))

    def evaluate(self, evaluator, params):
        raise NotImplementedError


def rangable(f):
    @wraps(f)
    def wrapped(self, evaluator, params):
        needed = len(params) == len(self.params) + 2

        if needed:
            old_range = evaluator.range
            new_range = params[len(self.params):]

            for i, item in enumerate(new_range):
                if item is None:
                    new_range[i] = old_range[i]
                else:
                    new_range[i] = parse_isoformat_date(item)

            evaluator.range = new_range

        result = f(self, evaluator, params[:len(self.params)])

        if needed:
            evaluator.range = old_range

        return result

    return wrapped
