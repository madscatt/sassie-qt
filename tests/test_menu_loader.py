from pathlib import Path

from sassie_qt.menu_loader import (
    DEFAULT_GENAPP_ZAZZIE_ROOT,
    DEFAULT_ZAZZIE_ROOT,
    find_gui_mimic_path,
    load_menu,
    load_module_definition,
)


def test_load_menu_includes_tools_modules():
    groups = load_menu(DEFAULT_GENAPP_ZAZZIE_ROOT)
    tools = next(group for group in groups if group.id == "tools")

    assert [module.id for module in tools.modules] == [
        "align",
        "data_interpolation",
        "extract_utilities",
        "merge_utilities",
    ]


def test_load_menu_includes_all_canonical_sections():
    groups = load_menu(DEFAULT_GENAPP_ZAZZIE_ROOT)

    assert {group.id: [module.id for module in group.modules] for group in groups} == {
        "tools": [
            "align",
            "data_interpolation",
            "extract_utilities",
            "merge_utilities",
        ],
        "build": ["build_utilities", "pdbscan", "pdbrx"],
        "contrast": [
            "contrast_calculator",
            "multi_component_analysis",
            "contrast_variation_analysis",
            "rg_center_of_mass_distance_calculator",
        ],
        "simulate": [
            "torsion_angle_monte_carlo",
            "monomer_monte_carlo",
            "complex_monte_carlo",
            "energy_minimization",
            "openmm",
            "torsion_angle_md",
            "prody",
        ],
        "calculate": ["sascalc", "sld_mol", "em_to_sas", "asaxs", "capriqorn"],
        "analyze": [
            "chi_square_filter",
            "density_plot",
            "apbs",
            "hullradsas",
            "bayesian_ensemble_estimator",
            "eros",
            "altens",
        ],
        "admin": [
            "jobmonitor",
            "jobshistory_1",
        ],
        "etc": ["sys_file_manager"],
    }


def test_load_module_definition_reads_data_interpolation_fields():
    module = load_module_definition("data_interpolation", DEFAULT_GENAPP_ZAZZIE_ROOT)

    assert module is not None
    assert module.id == "data_interpolation"
    assert any(field.id == "data_file_name" for field in module.fields)
    run_name = next(field for field in module.fields if field.id == "run_name")
    assert "results will be placed" in run_name.help_text
    assert "<br>" not in run_name.help_text
    assert "\nNote that only alphanumeric" in run_name.help_text


def test_load_module_definition_reads_non_tools_root_module_json():
    module = load_module_definition("build_utilities", DEFAULT_GENAPP_ZAZZIE_ROOT)

    assert module is not None
    assert module.path == DEFAULT_GENAPP_ZAZZIE_ROOT / "modules" / "build_utilities.json"
    assert any(field.id == "build_utilities_listbox" for field in module.fields)


def test_find_gui_mimic_path_prefers_exact_module_name():
    path = find_gui_mimic_path("align", DEFAULT_ZAZZIE_ROOT)

    assert path == Path(
        "/Users/curtisj/git_working_copies/zazzie/src/sassie/tools/align/gui_mimic_align.py"
    )
