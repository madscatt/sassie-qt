from pathlib import Path

from sassie_qt.modules.complex_monte_carlo.runner import ComplexMonteCarloRunner
from sassie_qt.modules.energy_minimization.runner import EnergyMinimizationRunner
from sassie_qt.modules.monomer_monte_carlo.runner import MonomerMonteCarloRunner
from sassie_qt.modules.openmm.runner import OpenMMRunner
from sassie_qt.modules.prody.runner import ProdyRunner
from sassie_qt.modules.torsion_angle_md.runner import TorsionAngleMDRunner
from sassie_qt.modules.torsion_angle_monte_carlo.runner import (
    TorsionAngleMonteCarloRunner,
)


MODULE_DATA = Path(__file__).resolve().parents[1] / "sassie_qt" / "modules"


def test_simulate_runners_validate_against_local_fixtures(tmp_path):
    for runner, form_values in _simulate_runner_forms():
        variables = runner.prepare_variables(tmp_path, form_values)
        runner.validate_variables(variables, tmp_path)


def test_monomer_monte_carlo_runner_writes_dcd(tmp_path):
    runner = MonomerMonteCarloRunner()
    form_values = _monomer_form()
    form_values["trials"] = "1"

    result = runner.run(tmp_path, form_values)

    assert result.run_path == tmp_path / "run_0" / "monomer_monte_carlo"
    assert result.run_path / "run_0.dcd.stats" in result.output_files
    assert (result.run_path / "run_0.dcd.stats").exists()


def test_prody_runner_creates_module_or_reports_missing_optional_dependency(tmp_path):
    runner = ProdyRunner()
    variables = runner.prepare_variables(tmp_path, _prody_form())
    runner.validate_variables(variables, tmp_path)

    try:
        sassie_module = runner.create_sassie_module()
    except RuntimeError as error:
        assert "ProDy is not installed" in str(error)
    else:
        assert hasattr(sassie_module, "main")


def _simulate_runner_forms():
    return [
        (MonomerMonteCarloRunner(), _monomer_form()),
        (ComplexMonteCarloRunner(), _complex_form()),
        (TorsionAngleMonteCarloRunner(), _torsion_angle_monte_carlo_form()),
        (TorsionAngleMDRunner(), _torsion_angle_md_form()),
        (EnergyMinimizationRunner(), _energy_minimization_form()),
        (OpenMMRunner(), _openmm_form()),
        (ProdyRunner(), _prody_form()),
    ]


def _monomer_form():
    local_data = MODULE_DATA / "monomer_monte_carlo" / "local_data"
    return {
        "runname": "run_0",
        "pdbfile": str(local_data / "gag_start.pdb"),
        "dcdfile": "run_0.dcd",
        "trials": "1",
        "goback": "1",
        "temp": "300.0",
        "moltype_list_box": "c1",
        "numranges": "5",
        "reslow": "123-144,277-282,354-374,378-389,408-412",
        "dtheta": "30.0,30.0,30.0,30.0,30.0",
        "residue_alignment": "284-350",
        "overlap_list_box": "c1",
    }


def _complex_form():
    local_data = MODULE_DATA / "complex_monte_carlo" / "local_data"
    return {
        "runname": "run_0",
        "pdbfile": str(local_data / "pai_vn_start.pdb"),
        "dcdfile": "run_0.dcd",
        "trials": "1",
        "goback": "1",
        "temp": "300.0",
        "nsegments": "2",
        "npsegments": "1",
        "moltype": "c1",
        "flpsegname": "VN1",
        "numranges": "1",
        "srlow": "40-129",
        "sith": "30.0",
        "seg_align": "1-39",
        "overlap_list_box": "c1",
    }


def _torsion_angle_monte_carlo_form():
    local_data = MODULE_DATA / "torsion_angle_monte_carlo" / "local_data"
    return {
        "run_name": "run_0",
        "pdbfile": str(local_data / "ten_mer.pdb"),
        "psffile": str(local_data / "ten_mer.psf"),
        "dcdfile": "run_0.dcd",
        "trial_steps": "1",
        "goback": "1",
        "temperature": "300.0",
        "number_of_flexible_regions": "1",
        "rotation_type_array": "c1",
        "rotation_direction_array": "c1",
        "basis_string_array": "resid >= 3 and resid < 5",
        "post_basis_string_array": "resid>=5 and resid<=10",
        "delta_theta_array": "30.0",
        "overlap_list_box": "c1",
    }


def _torsion_angle_md_form():
    local_data = MODULE_DATA / "torsion_angle_md" / "local_data"
    return {
        "runname": "run_0",
        "pdbfile": str(local_data / "hiv1_gag_ma.pdb"),
        "infile": str(local_data / "hiv1_gag_ma.pdb"),
        "outfile": "hiv1_gag_ma.dcd",
        "pretamd_min_steps": "1",
        "nsteps": "1",
        "temperature": "300.0",
        "rgforce": "0",
        "rgvalue": "0",
        "number_flexible_segments": "1",
        "all_moltype": "c1",
        "all_flexible_segnames": "MA",
        "all_snumranges": "1",
        "residue_ranges": "114-134",
    }


def _energy_minimization_form():
    local_data = MODULE_DATA / "energy_minimization" / "local_data"
    return {
        "runname": "run_0",
        "pdbfile": str(local_data / "ten_mer.pdb"),
        "infile": str(local_data / "ten_mer.pdb"),
        "psffile": str(local_data / "ten_mer.psf"),
        "outfile": "min_ten_mer.dcd",
        "ncpu": "1",
        "keepout_list_box": "c1",
        "md_list_box": "c1",
        "nsteps_1": "20",
    }


def _openmm_form():
    local_data = MODULE_DATA / "openmm" / "local_data"
    return {
        "runname": "run_0",
        "pdbfile": str(local_data / "ssdna.pdb"),
        "infile": str(local_data / "ssdna.pdb"),
        "psffile": str(local_data / "ssdna.psf"),
        "outfile": "openmm_ssdna.dcd",
        "ncpu": "1",
        "keepout_list_box": "c1",
        "nsteps": "1",
        "md_list_box": "c1",
    }


def _prody_form():
    local_data = MODULE_DATA / "prody" / "local_data"
    return {
        "run_name": "run_0",
        "pdbfile": str(local_data / "hivr.pdb"),
        "number_modes": "1",
        "number_conformations_samp": "1",
        "number_steps_traverse": "1",
        "rmsd_conformations_samp": "1.0",
        "rmsd_traverse": "1.5",
    }
