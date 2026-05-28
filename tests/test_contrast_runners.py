from pathlib import Path

from sassie_qt.modules.contrast_calculator.runner import ContrastCalculatorRunner
from sassie_qt.modules.contrast_variation_analysis.runner import (
    ContrastVariationAnalysisRunner,
)
from sassie_qt.modules.multi_component_analysis.runner import (
    MultiComponentAnalysisRunner,
)
from sassie_qt.modules.rg_center_of_mass_distance_calculator.runner import (
    RgCenterOfMassDistanceCalculatorRunner,
)


MODULE_DATA = Path(__file__).resolve().parents[1] / "sassie_qt" / "modules"


def test_contrast_runners_validate_against_local_fixtures(tmp_path):
    for runner, form_values in _contrast_runner_forms():
        variables = runner.prepare_variables(tmp_path, form_values)
        runner.validate_variables(variables, tmp_path)


def test_contrast_calculator_runner_writes_outputs(tmp_path):
    result = ContrastCalculatorRunner().run(tmp_path, _contrast_calculator_form())

    assert result.run_path == tmp_path / "run_0" / "contrast_calculator"
    assert result.run_path / "vnpai_general.txt" in result.output_files
    assert (result.run_path / "vnpai_general.txt").exists()


def test_multi_component_analysis_runner_writes_match_point_outputs(tmp_path):
    result = MultiComponentAnalysisRunner().run(tmp_path, _mca_match_point_form())

    assert result.run_path == tmp_path / "run_0" / "multi_component_analysis"
    assert result.run_path / "match_point" / "general_output_file.txt" in result.output_files
    assert (result.run_path / "match_point" / "general_output_file.txt").exists()


def test_multi_component_analysis_runner_writes_decomposition_outputs(tmp_path):
    result = MultiComponentAnalysisRunner().run(tmp_path, _mca_decomposition_form())

    assert result.run_path == tmp_path / "run_0" / "multi_component_analysis"
    assert result.run_path / "decomposition" / "general_output_file.txt" in result.output_files
    assert (result.run_path / "decomposition" / "i11_run_0.dat").exists()


def test_contrast_variation_analysis_runner_writes_outputs(tmp_path):
    result = ContrastVariationAnalysisRunner().run(tmp_path, _cva_form())

    assert result.run_path == tmp_path / "run_0" / "contrast_variation_analysis"
    assert result.run_path / "cva_fit_summary.json" in result.output_files
    assert (result.run_path / "cva_fit_summary.json").exists()


def test_rg_center_of_mass_distance_calculator_runner_writes_output(tmp_path):
    result = RgCenterOfMassDistanceCalculatorRunner().run(tmp_path, _rgcmd_form())

    assert result.run_path == tmp_path / "run_0" / "rg_center_of_mass_distance_calculator"
    assert result.output_files == (
        result.run_path / "pai_vn_2_frames_rgdist_pdb.txt",
    )
    assert result.output_files[0].exists()


def _contrast_runner_forms():
    return [
        (ContrastCalculatorRunner(), _contrast_calculator_form()),
        (MultiComponentAnalysisRunner(), _mca_match_point_form()),
        (MultiComponentAnalysisRunner(), _mca_decomposition_form()),
        (ContrastVariationAnalysisRunner(), _cva_form()),
        (RgCenterOfMassDistanceCalculatorRunner(), _rgcmd_form()),
    ]


def _contrast_calculator_form():
    local_data = MODULE_DATA / "contrast_calculator" / "local_data"
    return {
        "run_name": "run_0",
        "output_file_name": "vnpai",
        "number_of_input_files": "2",
        "input_file_names": ",".join(
            [
                str(local_data / "vn_seq.txt"),
                str(local_data / "pai_seq.txt"),
            ]
        ),
        "number_of_units": "1,1",
        "fraction_deuterated": "0,0.6",
        "molecule_type": "c3,c3",
        "is_fasta": "c2,c2",
        "solute_concentration": "8.0",
        "d2o_step": "5",
        "protein_exchange_fraction": "0.95",
        "nucleic_acid_exchange_fraction": "1.0",
        "number_of_solvent_components": "0",
        "number_of_additional_solute_components": "0",
    }


def _mca_match_point_form():
    return {
        "run_name": "run_0",
        "output_file_name": "general_output_file.txt",
        "multi_component_analysis_listbox": "c1",
        "number_of_contrast_points_match_point": "4",
        "fraction_d2o_match_point": "0.0,0.2,0.85,1.0",
        "izero_match_point": "0.85,0.534,0.013,0.095",
        "izero_error_match_point": "0.01,0.044,0.003,0.002",
        "concentration_match_point": "7.7,7.7,7.7,7.7",
        "concentration_error_match_point": "0.4,0.4,0.4,0.4",
        "initial_match_point_guess_flag": "false",
    }


def _mca_decomposition_form():
    local_data = MODULE_DATA / "multi_component_analysis" / "local_data"
    return {
        "run_name": "run_0",
        "output_file_name": "general_output_file.txt",
        "multi_component_analysis_listbox": "c3",
        "number_of_contrast_points_decomposition": "4",
        "fraction_d2o_decomposition": "0.0,0.2,0.85,1.0",
        "data_file_name_decomposition": ",".join(
            str(local_data / name)
            for name in ["0p.dat", "20p.dat", "85p1.dat", "100p1.dat"]
        ),
        "concentration_decomposition": "7.7,7.7,7.7,7.7",
        "concentration_error_decomposition": "0.4,0.4,0.4,0.4",
        "number_of_components_decomposition": "2",
        "component_name_decomposition": "vn,pai",
        "q_rg_limit_guinier": "1.3",
        "starting_data_point_guinier": "1,1,1,1",
        "initial_points_to_use_guinier": "6,6,6,6",
        "refine_scale_factor_flag": "c1",
        "verbose_output_flag": "false",
        "initial_guess_guinier": "1.0,1.0",
        "signal_to_noise_amplitude": "50.0,50.0,50.0,50.0",
        "partial_specific_volume_decomposition": "0.73,0.73",
        "molecular_weight_decomposition": "14.3,44.2",
        "delta_rho_decomposition": "2.551,5.104;1.383,3.928;-2.415,0.109;-3.292,-0.773",
    }


def _cva_form():
    local_data = MODULE_DATA / "contrast_variation_analysis" / "local_data"
    return {
        "run_name": "run_0",
        "sascalc_hdf5_file": str(local_data / "sascalc.h5"),
        "number_of_contrast_points": "3",
        "experimental_data_files": ",".join(
            str(local_data / name)
            for name in [
                "experimental_01.dat",
                "experimental_02.dat",
                "experimental_03.dat",
            ]
        ),
        "experimental_sources": "neutron,neutron,xray",
        "d2o_percentages": "0.0,85.0,0.0",
        "intensity_mode": "normalized",
        "scale_mode": "none",
        "contrast_weights": "1.0,1.0,1.0",
        "fit_ensemble_flag": "false",
    }


def _rgcmd_form():
    local_data = MODULE_DATA / "rg_center_of_mass_distance_calculator" / "local_data"
    return {
        "run_name": "run_0",
        "pdb_file_name": str(local_data / "pai_vn_start.pdb"),
        "trajectory_file_name": str(local_data / "pai_vn_2_frames.pdb"),
        "number_of_components": "2",
        "component_name": "VN,PAI",
        "basis_string": "segname VN1,segname PAI1",
        "number_of_weight_files": "0",
        "weight_file_names": "",
        "weight_basis_string": "",
    }
