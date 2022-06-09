from z3 import *

###### Z3-Solver
def gen_assign(solver, X):
    if solver.check() == z3.sat:  # Satisfiable
        model = solver.model()  # Gen model
        assign = {x.name: x.decode(model) for x in X}  # Fetch one satisfying assignment
        # could check for the size of code here
        assign_c = z3.Or([x.var != model[x.var] for x in X])  # Add counter constraint
        solver.add(assign_c)

        return solver, assign

    return solver, None


def gen_all(solver, X, MAX_NUM=100000):
    values = []

    while True:
        if len(values) > MAX_NUM:
            return values
        solver, assign = gen_assign(solver, X)
        if assign:
            values.append(assign)
        else:
            break

    return values

