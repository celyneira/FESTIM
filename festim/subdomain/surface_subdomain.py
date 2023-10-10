from dolfinx import fem
import numpy as np


class SurfaceSubdomain1D:
    """
    Subdomain class
    Attributes:

    """

    def __init__(self, id=None, x=None) -> None:
        """Inits Mesh
        Args:
            id (int): the id of the surface subdomain
            x (float): the x coordinate of the surface subdomain
        """
        self.id = id
        self.x = x
        self.dofs = None

    def locate_dof(self, function_space):
        """Creates smth"""
        dofs = fem.locate_dofs_geometrical(
            function_space, lambda x: np.isclose(x[0], self.x)
        )
        return dofs[0]
