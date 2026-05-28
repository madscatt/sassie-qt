import tarfile
from pathlib import Path

from sassie_qt.modules.altens.runner import AltensRunner
from sassie_qt.modules.apbs.runner import ApbsRunner
from sassie_qt.modules.bayesian_ensemble_estimator.runner import (
    BayesianEnsembleEstimatorRunner,
)
from sassie_qt.modules.chi_square_filter.runner import ChiSquareFilterRunner
from sassie_qt.modules.density_plot.runner import DensityPlotRunner
from sassie_qt.modules.eros.runner import ErosRunner
from sassie_qt.modules.hullradsas.runner import HullRadSasRunner


MODULE_DATA = Path(__file__).resolve().parents[1] / "sassie_qt" / "modules"


def test_analyze_runners_validate_against_local_fixtures(tmp_path):
    for runner, form_values in _analyze_runner_forms(tmp_path):
        variables = runner.prepare_variables(tmp_path, form_values)
        runner.validate_variables(variables, tmp_path)


def test_hullradsas_runner_writes_outputs(tmp_path):
    result = HullRadSasRunner().run(tmp_path, _hullradsas_form())

    assert result.run_path == tmp_path / "run_0" / "hullradsas"
    assert result.run_path / "hullradsas.dat" in result.output_files
    assert (result.run_path / "hullradsas.dat").exists()


def test_chi_square_filter_runner_writes_outputs(tmp_path):
    result = ChiSquareFilterRunner().run(tmp_path, _chi_square_filter_form(tmp_path))

    assert result.run_path == tmp_path / "run_0" / "chi_square_filter"
    assert result.run_path / "chi_square_filter_plots.json" in result.output_files
    assert (result.run_path / "chi_square_filter_plots.json").exists()


def test_altens_runner_writes_outputs(tmp_path):
    result = AltensRunner().run(tmp_path, _altens_form())

    assert result.run_path == tmp_path / "run_0" / "altens"
    assert result.output_files


def test_eros_runner_writes_outputs(tmp_path):
    result = ErosRunner().run(tmp_path, _eros_form())

    assert result.run_path == tmp_path / "run_0" / "eros"
    assert result.output_files


def _analyze_runner_forms(tmp_path):
    return [
        (AltensRunner(), _altens_form()),
        (ApbsRunner(), _apbs_form()),
        (BayesianEnsembleEstimatorRunner(), _bees_form()),
        (ChiSquareFilterRunner(), _chi_square_filter_form(tmp_path)),
        (DensityPlotRunner(), _density_plot_form()),
        (ErosRunner(), _eros_form()),
        (HullRadSasRunner(), _hullradsas_form()),
    ]


def _altens_form():
    local_data = MODULE_DATA / "altens" / "local_data"
    return {
        "run_name": "run_0",
        "rdc_input_file": str(local_data / "test_rdc_nh_caha_exclude_pro.txt"),
        "pdbfile": str(local_data / "1D3Z_1frame.pdb"),
        "dcdfile": str(local_data / "1D3Z_1frame.pdb"),
        "residue_list_file_flag": "false",
        "residue_list_file": str(local_data / "reslist_Ub.txt"),
        "use_monte_carlo_flag": "true",
        "number_of_monte_carlo_steps": "1",
        "seed": "1,123",
    }


def _apbs_form():
    local_data = MODULE_DATA / "apbs" / "local_data"
    return {
        "runname": "run_0",
        "pdbfile": str(local_data / "ten_mer.pdb"),
        "infile": str(local_data / "ten_mer.pdb"),
        "ph": "5.5",
        "temp": "300.0",
        "ion_conc": "0.15",
        "ion_charge": "1.0",
        "ion_radius": "1.62",
    }


def _bees_form():
    local_data = MODULE_DATA / "bayesian_ensemble_estimator" / "local_data"
    return {
        "runname": "bees_gui_mimic",
        "sas_data": str(local_data / "ubq_saxs.dat"),
        "theoretical_profiles_zip": str(local_data / "QuickTest.zip"),
        "posterior_burn": "1",
        "max_iterations": "2",
        "number_of_MCs": "1",
        "nproc": "1",
        "d_max": "83.6",
        "random_seed": "12345",
    }


def _chi_square_filter_form(tmp_path):
    local_data = MODULE_DATA / "chi_square_filter" / "local_data"
    sascalc_path = _extract_chi_square_sascalc_fixture(tmp_path)
    return {
        "run_name": "run_0",
        "number_of_contrast_points": "1",
        "fraction_d2o": "1.0",
        "sasintfiles": str(local_data / "K48_UBA2_org.dat"),
        "saspaths": str(sascalc_path),
        "io": "0.1229",
        "sastype_list_box": "c0",
        "reduced_x2_list_box": "c1",
        "number_of_weight_files": "0",
        "basis_string": "",
        "weight_file_names": "",
        "global_weight_file_flag": "false",
    }


def _extract_chi_square_sascalc_fixture(tmp_path):
    archive = (
        MODULE_DATA
        / "chi_square_filter"
        / "local_data"
        / "diUb_sascalc_neutron_D2Op_100.tar.gz"
    )
    sascalc_path = tmp_path / "chi_square_filter_sascalc" / "neutron_D2Op_100"
    if sascalc_path.exists():
        return sascalc_path
    sascalc_path.mkdir(parents=True)
    with tarfile.open(archive, "r:gz") as tar_file:
        tar_file.extractall(sascalc_path)
    for apple_double_file in sascalc_path.glob("._*"):
        apple_double_file.unlink()
    return sascalc_path


def _density_plot_form():
    local_data = MODULE_DATA / "density_plot" / "local_data"
    return {
        "run_name": "run_0",
        "pdbfile": str(local_data / "hiv1_gag.pdb"),
        "dcdfile": str(local_data / "hiv1_gag_20_frames.dcd"),
        "ofile": "test",
        "box_lengths": "100,100,100",
        "gridsp": "5.0",
        "save_occupancy_list_box": "c1",
        "nsegments": "1",
        "sname": "GAG",
        "nregions": "1",
        "residue_regions": "6-123",
        "sbasis": "CA",
        "weight_flag_check_box": "false",
    }


def _eros_form():
    local_data = MODULE_DATA / "eros" / "local_data"
    return {
        "run_name": "run_0",
        "goal_iq_data_file": str(local_data / "rsvf_0d_saxs_int_short.dat"),
        "iq_data_archive": str(local_data / "eros_iq_profiles.tar.gz"),
        "io": "1.0",
        "number_of_files_to_use": "5",
        "number_of_monte_carlo_steps": "1",
        "weight_step_size_fraction": "0.1",
        "theta": "0.0",
        "beta": "100.0",
        "reduced_x2_list_box": "c1",
        "seed": "1,123",
    }


def _hullradsas_form():
    local_data = MODULE_DATA / "hullradsas" / "local_data"
    return {
        "run_name": "run_0",
        "pdbfile": str(local_data / "c.pdb"),
        "infile": str(local_data / "c.pdb"),
        "ofile": "hullradsas.dat",
        "timeseries_file": "hullradsas_timeseries.tsv",
        "stats_file": "hullradsas_stats.tsv",
    }
