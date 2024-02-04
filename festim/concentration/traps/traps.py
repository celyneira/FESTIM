import festim
import fenics as f
import warnings


class Traps(list):
    """
    A list of festim.Trap objects
    """

    def __init__(self, *args):
        # checks that input is list
        try:
            super().__init__(*args)
        except:
            raise TypeError("festim.Traps must be a list")

        # checks that list elements are festim.Export
        if len(self) != 0:
            if not all(isinstance(t, festim.Trap) for t in self):
                raise TypeError("festim.Traps must be a list of festim.Trap")

        self.F = None
        self.extrinsic_formulations = []
        self.sub_expressions = []

        # add ids if unspecified
        for i, trap in enumerate(self, 1):
            if trap.id is None:
                trap.id = i

    @property
    def traps(self):
        warnings.warn(
            "The traps attribute will be deprecated in a future release, please use festim.Traps[:] instead",
            DeprecationWarning,
        )
        return self

    def make_traps_materials(self, materials):
        for trap in self:
            trap.make_materials(materials)

    def create_forms(self, mobile, materials, T, dx, dt=None):
        self.F = 0
        for trap in self:
            trap.create_form(mobile, materials, T, dx, dt=dt)
            self.F += trap.F
            self.sub_expressions += trap.sub_expressions

    def get_trap(self, id):
        for trap in self:
            if trap.id == id:
                return trap
        raise ValueError("Couldn't find trap {}".format(id))

    def initialise_extrinsic_traps(self, V):
        """Add functions to ExtrinsicTrapBase objects for density form"""
        for trap in self:
            if isinstance(trap, festim.ExtrinsicTrapBase):
                trap.density = [f.Function(V)]
                trap.density_test_function = f.TestFunction(V)
                trap.density_previous_solution = f.project(f.Constant(0), V)

    def define_variational_problem_extrinsic_traps(self, dx, dt, T):
        """
        Creates the variational formulations for the extrinsic traps densities

        Args:
            dx (fenics.Measure): the dx measure of the sim
            dt (festim.Stepsize): If None assuming steady state.
            T (festim.Temperature): the temperature of the simulation
        """
        self.extrinsic_formulations = []
        expressions_extrinsic = []
        for trap in self:
            if isinstance(trap, festim.ExtrinsicTrapBase):
                trap.create_form_density(dx, dt, T)
                self.extrinsic_formulations.append(trap.form_density)
        self.sub_expressions.extend(expressions_extrinsic)

    def solve_extrinsic_traps(self):
        for trap in self:
            if isinstance(trap, festim.ExtrinsicTrapBase):
                du_t = f.TrialFunction(trap.density[0].function_space())
                J_t = f.derivative(trap.form_density, trap.density[0], du_t)
                problem = f.NonlinearVariationalProblem(
                    trap.form_density, trap.density[0], [], J_t
                )
                solver = f.NonlinearVariationalSolver(problem)
                solver.parameters["newton_solver"][
                    "absolute_tolerance"
                ] = trap.absolute_tolerance
                solver.parameters["newton_solver"][
                    "relative_tolerance"
                ] = trap.relative_tolerance
                solver.parameters["newton_solver"][
                    "maximum_iterations"
                ] = trap.maximum_iterations
                solver.parameters["newton_solver"]["linear_solver"] = trap.linear_solver
                solver.solve()

    def update_extrinsic_traps_density(self):
        for trap in self:
            if isinstance(trap, festim.ExtrinsicTrapBase):
                trap.density_previous_solution.assign(trap.density[0])
