from pathlib import Path

import sassie.util.sassie_config as sassie_config

from sassie_qt.modules.build_utilities.runner import BuildUtilitiesRunner
from sassie_qt.modules.pdbscan.runner import PDBScanRunner
from sassie_qt.modules.pdbrx.runner import PDBRxRunner


MODULE_DATA = Path(__file__).resolve().parents[1] / "sassie_qt" / "modules"


def test_build_utilities_runner_writes_transformed_pdb(tmp_path):
    local_data = MODULE_DATA / "build_utilities" / "local_data"

    result = BuildUtilitiesRunner().run(
        tmp_path,
        {
            "run_name": "run_0",
            "build_utilities_listbox": "c1",
            "input_pdbfile": str(local_data / "hiv1_gag.pdb"),
            "pdb_choices_listbox": "c4",
            "translation_rotation_output_filename": "transformed.pdb",
            "center_checkbox": "false",
            "delta_x": "0",
            "delta_y": "0",
            "delta_z": "0",
            "rotation_axes_listbox": "c1",
        },
    )

    assert result.run_path == tmp_path / "run_0" / "build_utilities"
    assert result.output_files == (result.run_path / "transformed.pdb",)
    assert result.output_files[0].exists()


def test_build_utilities_runner_writes_fasta_sequence_pdb(tmp_path):
    result = BuildUtilitiesRunner().run(
        tmp_path,
        {
            "run_name": "run_0",
            "build_utilities_listbox": "c2",
            "fasta_output_filename": "sequence_from_fasta.pdb",
            "fasta_moltype_listbox": "c1",
            "fasta_listbox": "c1",
            "fasta_input_sequence": "RRAGMPSCYLK",
        },
    )

    assert result.output_files == (result.run_path / "sequence_from_fasta.pdb",)
    assert result.output_files[0].exists()


def test_pdbscan_runner_writes_report(tmp_path):
    local_data = MODULE_DATA / "pdbscan" / "local_data"

    result = PDBScanRunner().run(
        tmp_path,
        {
            "runname": "run_0",
            "pdbfile": str(local_data / "one_residue.pdb"),
        },
    )

    assert result.run_path == tmp_path / "run_0" / "pdbscan"
    assert (result.run_path / "one_residue.mkd").exists()


def test_pdbrx_runner_reaches_run_path(tmp_path):
    local_data = MODULE_DATA / "pdbrx" / "local_data"
    topfile = (
        Path(sassie_config.__bin_path__)
        / "toppar"
        / "top_all27_prot_na.inp"
    )

    result = PDBRxRunner().run(
        tmp_path,
        {
            "runname": "run_0",
            "pdbfile": str(local_data / "one_residue.pdb"),
            "topfile": str(topfile),
            "defaults": "true",
        },
    )

    assert result.run_path == tmp_path / "run_0" / "pdbrx"
    assert result.run_path.exists()
