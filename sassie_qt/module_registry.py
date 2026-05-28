"""Registry of SASSIE module runners available to the Qt prototype."""

from __future__ import annotations

from sassie_qt.modules.altens.runner import AltensRunner
from sassie_qt.modules.align.runner import AlignRunner
from sassie_qt.modules.apbs.runner import ApbsRunner
from sassie_qt.modules.bayesian_ensemble_estimator.runner import (
    BayesianEnsembleEstimatorRunner,
)
from sassie_qt.modules.build_utilities.runner import BuildUtilitiesRunner
from sassie_qt.modules.chi_square_filter.runner import ChiSquareFilterRunner
from sassie_qt.modules.complex_monte_carlo.runner import ComplexMonteCarloRunner
from sassie_qt.modules.contrast_calculator.runner import ContrastCalculatorRunner
from sassie_qt.modules.contrast_variation_analysis.runner import (
    ContrastVariationAnalysisRunner,
)
from sassie_qt.modules.data_interpolation.runner import DataInterpolationRunner
from sassie_qt.modules.density_plot.runner import DensityPlotRunner
from sassie_qt.modules.energy_minimization.runner import EnergyMinimizationRunner
from sassie_qt.modules.eros.runner import ErosRunner
from sassie_qt.modules.extract_utilities.runner import ExtractUtilitiesRunner
from sassie_qt.modules.hullradsas.runner import HullRadSasRunner
from sassie_qt.modules.merge_utilities.runner import MergeUtilitiesRunner
from sassie_qt.modules.monomer_monte_carlo.runner import MonomerMonteCarloRunner
from sassie_qt.modules.multi_component_analysis.runner import (
    MultiComponentAnalysisRunner,
)
from sassie_qt.modules.openmm.runner import OpenMMRunner
from sassie_qt.modules.pdbscan.runner import PDBScanRunner
from sassie_qt.modules.pdbrx.runner import PDBRxRunner
from sassie_qt.modules.prody.runner import ProdyRunner
from sassie_qt.modules.rg_center_of_mass_distance_calculator.runner import (
    RgCenterOfMassDistanceCalculatorRunner,
)
from sassie_qt.modules.torsion_angle_md.runner import TorsionAngleMDRunner
from sassie_qt.modules.torsion_angle_monte_carlo.runner import (
    TorsionAngleMonteCarloRunner,
)


MODULE_RUNNER_FACTORIES = {
    "align": AlignRunner,
    "altens": AltensRunner,
    "apbs": ApbsRunner,
    "bayesian_ensemble_estimator": BayesianEnsembleEstimatorRunner,
    "build_utilities": BuildUtilitiesRunner,
    "chi_square_filter": ChiSquareFilterRunner,
    "complex_monte_carlo": ComplexMonteCarloRunner,
    "contrast_calculator": ContrastCalculatorRunner,
    "contrast_variation_analysis": ContrastVariationAnalysisRunner,
    "data_interpolation": DataInterpolationRunner,
    "density_plot": DensityPlotRunner,
    "energy_minimization": EnergyMinimizationRunner,
    "eros": ErosRunner,
    "extract_utilities": ExtractUtilitiesRunner,
    "hullradsas": HullRadSasRunner,
    "merge_utilities": MergeUtilitiesRunner,
    "monomer_monte_carlo": MonomerMonteCarloRunner,
    "multi_component_analysis": MultiComponentAnalysisRunner,
    "openmm": OpenMMRunner,
    "pdbscan": PDBScanRunner,
    "pdbrx": PDBRxRunner,
    "prody": ProdyRunner,
    "rg_center_of_mass_distance_calculator": RgCenterOfMassDistanceCalculatorRunner,
    "torsion_angle_md": TorsionAngleMDRunner,
    "torsion_angle_monte_carlo": TorsionAngleMonteCarloRunner,
}
