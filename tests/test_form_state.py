from sassie_qt.form_state import FormStateEngine
from sassie_qt.menu_loader import load_module_definition


def test_extract_utilities_repeater_and_conditional_visibility():
    engine = _engine("extract_utilities")

    state = engine.evaluate(
        {
            "trajectory_checkbox": "true",
            "option_list_box": "c4",
            "sas_checkbox": "true",
            "number_of_sas_paths": "3",
        }
    )

    assert state.fields["pdb_filename"].visible
    assert state.fields["local_value_c4"].visible
    assert not state.fields["local_value_c1"].visible
    assert state.fields["sas_paths"].visible
    assert state.fields["sas_paths"].repeat_count == 3
    assert state.fields["sas_paths"].ordinary_integer_repeater


def test_merge_utilities_syncs_hidden_integer_repeater_controller():
    engine = _engine("merge_utilities")

    state = engine.evaluate(
        {
            "trajectory_checkbox": "true",
            "number_of_runs_to_merge": "4",
        }
    )

    assert state.values["number_of_trajectories"] == "4"
    assert not state.fields["number_of_trajectories"].visible
    assert state.fields["trajectory_names"].repeat_count == 4
    assert state.fields["trajectory_names"].ordinary_integer_repeater


def test_build_utilities_listbox_condition_and_repeat_counts():
    engine = _engine("build_utilities")

    state = engine.evaluate(
        {
            "pdb_choices_listbox": "c2",
            "number_of_constraint_files": "3",
            "build_utilities_listbox": "c2",
            "fasta_listbox": "c2",
        }
    )

    assert state.fields["constraint_listbox"].repeat_count == 3
    assert state.fields["constraint_pdb_files"].repeat_count == 3
    assert not state.fields["input_pdbfile"].visible
    assert state.fields["fasta_output_filename"].visible
    assert not state.fields["fasta_input_sequence"].visible
    assert state.fields["fasta_input_file"].visible


def test_contrast_integer_pair_dimensions_and_headers():
    engine = _engine("multi_component_analysis")

    state = engine.evaluate(
        {
            "multi_component_analysis_listbox": "c3",
            "number_of_contrast_points_decomposition": "3",
            "number_of_components_decomposition": "2",
            "fraction_d2o_decomposition": "0.0,0.2,0.85",
            "component_name_decomposition": "vn,pai",
        }
    )

    delta_rho = state.fields["delta_rho_decomposition"]
    assert delta_rho.visible
    assert delta_rho.integer_pair_repeater
    assert delta_rho.integer_pair_dimensions == (3, 2)
    assert delta_rho.integer_pair_headers == (
        ["0.0", "0.2", "0.85"],
        ["vn", "pai"],
    )


def test_chi_square_nested_weight_fields_are_not_ordinary_repeaters():
    engine = _engine("chi_square_filter")

    state = engine.evaluate(
        {
            "number_of_contrast_points": "2",
            "number_of_weight_files": "2,1",
        }
    )

    assert state.fields["fraction_d2o"].repeat_count == 2
    assert state.fields["number_of_weight_files"].repeat_count == 2
    assert state.fields["number_of_weight_files"].ordinary_integer_repeater
    assert state.fields["basis_string"].repeat_count == 1
    assert not state.fields["basis_string"].ordinary_integer_repeater
    assert state.fields["weight_file_names"].repeat_count == 1
    assert not state.fields["weight_file_names"].ordinary_integer_repeater


def _engine(module_id: str) -> FormStateEngine:
    module_definition = load_module_definition(module_id)
    assert module_definition is not None
    return FormStateEngine(module_definition.fields)
