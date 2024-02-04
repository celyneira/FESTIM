from festim import (
    DerivedQuantities,
    SurfaceFlux,
    AverageVolume,
    TotalSurface,
    TotalVolume,
    MaximumVolume,
    MinimumVolume,
    Materials,
)
import fenics as f
import os
from pathlib import Path
import pytest


class TestMakeHeader:
    my_derv_quant = None
    surface_flux_1 = SurfaceFlux("solute", 2)
    surface_flux_2 = SurfaceFlux("T", 3)
    average_vol_1 = AverageVolume("solute", 3)
    average_vol_2 = AverageVolume("T", 4)
    tot_surf_1 = TotalSurface("retention", 6)
    tot_surf_2 = TotalSurface("trap1", 7)
    tot_vol_1 = TotalVolume("trap2", 5)
    min_vol_1 = MinimumVolume("retention", 2)
    max_vol_1 = MaximumVolume("T", 2)

    @property
    def my_derv_quant(self):
        return self._my_derv_quant

    @my_derv_quant.setter
    def my_derv_quant(self, value):
        self._my_derv_quant = DerivedQuantities(value)

    def test_simple(self):
        self.my_derv_quant = [self.surface_flux_1]
        header = self.my_derv_quant.make_header()
        expected_header = ["t(s)", self.surface_flux_1.title]
        assert header == expected_header

    def test_two_quantities(self):
        self.my_derv_quant = [
            self.surface_flux_1,
            self.tot_surf_1,
        ]
        header = self.my_derv_quant.make_header()
        expected_header = ["t(s)", self.surface_flux_1.title, self.tot_surf_1.title]
        assert header == expected_header

    def test_all_quantities(self):
        self.my_derv_quant = [
            self.surface_flux_1,
            self.average_vol_1,
            self.tot_surf_1,
            self.tot_vol_1,
            self.min_vol_1,
            self.max_vol_1,
        ]
        header = self.my_derv_quant.make_header()
        expected_header = ["t(s)"] + [
            self.surface_flux_1.title,
            self.average_vol_1.title,
            self.tot_surf_1.title,
            self.tot_vol_1.title,
            self.min_vol_1.title,
            self.max_vol_1.title,
        ]
        assert header == expected_header


class TestAssignMeasuresToQuantities:
    my_quantities = DerivedQuantities(
        [
            SurfaceFlux("solute", 2),
            SurfaceFlux("T", 3),
            AverageVolume("solute", 3),
        ]
    )
    mesh = f.UnitIntervalMesh(10)
    vol_markers = f.MeshFunction("size_t", mesh, 1)
    dx = f.dx(subdomain_data=vol_markers)
    ds = f.ds()
    n = f.FacetNormal(mesh)
    my_quantities.assign_measures_to_quantities(dx, ds)

    def test_quantities_have_dx(self):
        for quantity in self.my_quantities:
            assert quantity.dx == self.dx

    def test_quantities_have_ds(self):
        for quantity in self.my_quantities:
            assert quantity.ds == self.ds

    def test_quantities_have_n(self):
        for quantity in self.my_quantities:
            assert quantity.n == self.n


class TestAssignPropertiesToQuantities:
    mesh = f.UnitIntervalMesh(10)
    V = f.FunctionSpace(mesh, "P", 1)
    my_quantities = DerivedQuantities(
        [
            SurfaceFlux("solute", 2),
            SurfaceFlux("T", 3),
            AverageVolume("solute", 3),
        ]
    )
    my_mats = Materials()
    my_mats.D = f.Function(V)
    my_mats.S = f.Function(V)
    my_mats.Q = f.Function(V)
    my_mats.thermal_cond = f.Function(V)
    T = f.Function(V)

    my_quantities.assign_properties_to_quantities(my_mats)

    def test_quantities_have_D(self):
        for quantity in self.my_quantities:
            assert quantity.D == self.my_mats.D

    def test_quantities_have_S(self):
        for quantity in self.my_quantities:
            assert quantity.S == self.my_mats.S

    def test_quantities_have_Q(self):
        for quantity in self.my_quantities:
            assert quantity.Q == self.my_mats.Q

    def test_quantities_have_thermal_cond(self):
        for quantity in self.my_quantities:
            assert quantity.thermal_cond == self.my_mats.thermal_cond


class TestCompute:
    my_derv_quant = None
    surface_flux_1 = SurfaceFlux("solute", 2)
    surface_flux_2 = SurfaceFlux("T", 3)
    average_vol_1 = AverageVolume("solute", 1)
    average_vol_2 = AverageVolume("T", 1)
    tot_surf_1 = TotalSurface("retention", 6)
    tot_surf_2 = TotalSurface("trap1", 7)
    tot_vol_1 = TotalVolume("trap1", 5)
    min_vol_1 = MinimumVolume("retention", 1)
    max_vol_1 = MaximumVolume("T", 1)

    mesh = f.UnitIntervalMesh(10)
    V = f.FunctionSpace(mesh, "P", 1)
    T = f.Function(V)
    label_to_function = {
        "solute": f.Function(V),
        "T": T,
        "retention": f.Function(V),
        "trap1": f.Function(V),
    }

    vol_markers = f.MeshFunction("size_t", mesh, 1, 1)
    left = f.CompiledSubDomain("near(x[0], 0) && on_boundary")
    right = f.CompiledSubDomain("near(x[0], 1) && on_boundary")
    surface_markers = f.MeshFunction("size_t", mesh, 0)
    left.mark(surface_markers, 1)
    right.mark(surface_markers, 2)
    dx = f.Measure("dx", domain=mesh, subdomain_data=vol_markers)
    ds = f.Measure("ds", domain=mesh, subdomain_data=surface_markers)
    n = f.FacetNormal(mesh)

    T = f.interpolate(f.Constant(2), V)
    my_mats = Materials()
    my_mats.D = f.interpolate(f.Constant(2), V)
    my_mats.S = f.interpolate(f.Constant(2), V)
    my_mats.H = f.interpolate(f.Constant(2), V)
    my_mats.thermal_cond = f.interpolate(f.Constant(2), V)

    @property
    def my_derv_quant(self):
        return self._my_derv_quant

    @my_derv_quant.setter
    def my_derv_quant(self, value):
        self._my_derv_quant = DerivedQuantities(value)

    def test_simple(self):
        self.my_derv_quant = [self.surface_flux_1]
        for quantity in self.my_derv_quant:
            quantity.function = self.label_to_function[quantity.field]
        self.my_derv_quant.assign_properties_to_quantities(self.my_mats)
        self.my_derv_quant.assign_measures_to_quantities(self.dx, self.ds)
        t = 2

        expected_data = [t] + [quantity.compute() for quantity in self.my_derv_quant]

        self.my_derv_quant.data = []
        self.my_derv_quant.compute(t)
        assert self.my_derv_quant.data[0] == expected_data

    def test_two_quantities(self):
        self.my_derv_quant = [
            self.surface_flux_1,
            self.average_vol_1,
        ]
        for quantity in self.my_derv_quant:
            quantity.function = self.label_to_function[quantity.field]
        self.my_derv_quant.assign_properties_to_quantities(self.my_mats)
        self.my_derv_quant.assign_measures_to_quantities(self.dx, self.ds)
        t = 2

        expected_data = [t] + [quantity.compute() for quantity in self.my_derv_quant]

        self.my_derv_quant.data = []
        self.my_derv_quant.compute(t)

        assert self.my_derv_quant.data[0] == expected_data

    def test_all_quantities(self):
        self.my_derv_quant = [
            self.surface_flux_1,
            self.average_vol_1,
            self.tot_surf_1,
            self.tot_vol_1,
            self.min_vol_1,
            self.max_vol_1,
        ]
        for quantity in self.my_derv_quant:
            quantity.function = self.label_to_function[quantity.field]
        self.my_derv_quant.assign_properties_to_quantities(self.my_mats)
        self.my_derv_quant.assign_measures_to_quantities(self.dx, self.ds)
        t = 2

        expected_data = [t]
        for quantity in self.my_derv_quant:
            if isinstance(quantity, (MaximumVolume, MinimumVolume)):
                expected_data.append(quantity.compute(self.vol_markers))
            else:
                expected_data.append(quantity.compute())

        self.my_derv_quant.data = []
        self.my_derv_quant.compute(t)

        assert self.my_derv_quant.data[0] == expected_data


class TestWrite:
    @pytest.fixture
    def folder(self, tmpdir):
        return str(Path(tmpdir.mkdir("test_folder")))

    @pytest.fixture
    def my_derived_quantities(self):
        filename = "my_file.csv"
        my_derv_quant = DerivedQuantities(filename=filename)
        my_derv_quant.data = [
            ["a", "b", "c"],
            [1, 2, 3],
            [1, 2, 3],
        ]
        return my_derv_quant

    def test_write(self, folder, my_derived_quantities):
        """adds data to DerivedQuantities and checks that write() creates the csv
        file
        """
        filename = "{}/my_file.csv".format(folder)
        my_derived_quantities.filename = filename
        my_derived_quantities.write()

        assert os.path.exists(filename)

    def test_write_folder_doesnt_exist(self, folder, my_derived_quantities):
        """Checks that write() creates the inexisting folder"""
        filename = "{}/folder2/my_file.csv".format(folder)
        my_derived_quantities.filename = filename
        my_derived_quantities.write()

        assert os.path.exists(filename)


class TestFilter:
    """Tests the filter method of DerivedQUantities"""

    def test_simple(self):
        flux1 = SurfaceFlux(field="solute", surface=1)
        flux2 = SurfaceFlux(field="T", surface=2)
        derived_quantities = DerivedQuantities([flux1, flux2])

        assert derived_quantities.filter(surfaces=[1, 2]) == [flux1, flux2]
        assert derived_quantities.filter(surfaces=[1]) == flux1
        assert derived_quantities.filter(fields=["T"]) == flux2
        assert derived_quantities.filter(fields=["T", "solute"], surfaces=[3]) == []
        assert derived_quantities.filter(fields=["solute"], surfaces=[1, 2]) == flux1

    def test_with_volumes(self):
        flux1 = SurfaceFlux(field="solute", surface=1)
        flux2 = SurfaceFlux(field="T", surface=2)
        total1 = TotalVolume(field="1", volume=3)
        total2 = TotalVolume(field="retention", volume=1)
        derived_quantities = DerivedQuantities([flux1, flux2, total1, total2])

        assert derived_quantities.filter() == derived_quantities
        assert derived_quantities.filter(surfaces=[1, 2], volumes=[3]) == []
        assert (
            derived_quantities.filter(volumes=[1, 3], fields=["retention", "solute"])
            == total2
        )

    def test_with_single_args(self):
        flux1 = SurfaceFlux(field="solute", surface=1)
        flux2 = SurfaceFlux(field="T", surface=2)
        total1 = TotalVolume(field="1", volume=3)

        derived_quantities = DerivedQuantities([flux1, flux2, total1])

        assert derived_quantities.filter(surfaces=1) == flux1
        assert derived_quantities.filter(fields="T") == flux2
        assert derived_quantities.filter(volumes=3) == total1

    def test_several_quantities_one_surface(self):
        surf1 = SurfaceFlux(field="solute", surface=1)
        surf2 = TotalSurface(field="solute", surface=1)
        derived_quantities = DerivedQuantities([surf1, surf2])

        assert derived_quantities.filter(surfaces=1, instances=SurfaceFlux) == surf1
        assert derived_quantities.filter(surfaces=1, instances=TotalSurface) == surf2
        assert derived_quantities.filter(
            surfaces=1, instances=[TotalSurface, SurfaceFlux]
        ) == [surf1, surf2]


def test_wrong_type_filename():
    """Checks that an error is raised when filename is not a string"""
    with pytest.raises(TypeError, match="filename must be a string"):
        DerivedQuantities(filename=2)


def test_filename_ends_with_csv():
    """Checks that an error is raised when filename doesn't end with .csv"""
    with pytest.raises(ValueError, match="filename must end with .csv"):
        DerivedQuantities(filename="coucou")


def test_set_derived_quantitites_wrong_type():
    """Checks an error is raised when festim.DerivedQuantities is set with the wrong type"""
    flux1 = SurfaceFlux(field="solute", surface=1)

    combinations = [flux1, "coucou", 1, True]

    for dq_combination in combinations:
        with pytest.raises(
            TypeError,
            match="festim.DerivedQuantities must be a list",
        ):
            DerivedQuantities(dq_combination)

    with pytest.raises(
        TypeError,
        match="festim.DerivedQuantities must be a list of festim.DerivedQuantity",
    ):
        DerivedQuantities([flux1, 2])
