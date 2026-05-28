from pathlib import Path

from sassie_qt.modules.align.runner import AlignRunner
from sassie_qt.modules.extract_utilities.runner import ExtractUtilitiesRunner
from sassie_qt.modules.merge_utilities.runner import MergeUtilitiesRunner


MODULE_DATA = Path(__file__).resolve().parents[1] / "sassie_qt" / "modules"


def test_align_runner_writes_aligned_dcd(tmp_path):
    local_data = MODULE_DATA / "align" / "local_data"

    result = AlignRunner().run(
        tmp_path,
        {
            "runname": "run_0",
            "pdbmol1": str(local_data / "hiv1_gag.pdb"),
            "pdbmol2": str(local_data / "hiv1_gag.pdb"),
            "infile": str(local_data / "hiv1_gag_20_frames.dcd"),
            "ofile": "aligned_hiv1_gag_20_frames.dcd",
            "basis1": "CA",
            "basis2": "CA",
            "lowres1": "145",
            "lowres2": "145",
            "highres1": "350",
            "highres2": "350",
            "ebasis1": "None",
            "ebasis2": "None",
            "zflag_check_box": "false",
            "zcutoff": "0.0",
        },
    )

    assert result.run_path == tmp_path / "run_0" / "align"
    assert result.output_files[0].exists()
    assert result.output_files[1].exists()


def test_extract_utilities_runner_writes_single_frame_pdb(tmp_path):
    local_data = MODULE_DATA / "extract_utilities" / "local_data"

    result = ExtractUtilitiesRunner().run(
        tmp_path,
        {
            "runname": "run_0",
            "trajectory_checkbox": "true",
            "sas_checkbox": "false",
            "pdb_filename": str(local_data / "hiv1_gag.pdb"),
            "trajectory_filename": str(local_data / "hiv1_gag_20_frames.dcd"),
            "output_filename": "frame_1_from_dcd.pdb",
            "option_list_box": "c1",
            "local_value_c1": "1",
        },
    )

    assert result.run_path == tmp_path / "run_0" / "extract_utilities"
    assert result.output_files == (result.run_path / "frame_1_from_dcd.pdb",)
    assert result.output_files[0].exists()


def test_merge_utilities_runner_writes_merged_dcd(tmp_path):
    local_data = MODULE_DATA / "merge_utilities" / "local_data"

    result = MergeUtilitiesRunner().run(
        tmp_path,
        {
            "runname": "run_0",
            "number_of_runs_to_merge": "2",
            "trajectory_checkbox": "true",
            "sas_checkbox": "false",
            "pdb_file": str(local_data / "hiv1_gag.pdb"),
            "trajectory_names": ",".join(
                [
                    str(local_data / "run_m1.dcd"),
                    str(local_data / "run_m2.dcd"),
                ]
            ),
            "output_filename": "all.dcd",
            "merge_option_list_box": "c1",
        },
    )

    assert result.run_path == tmp_path / "run_0" / "merge_utilities"
    assert result.output_files == (result.run_path / "all.dcd",)
    assert result.output_files[0].exists()
