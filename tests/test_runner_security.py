from __future__ import annotations

import tarfile
from pathlib import Path

import pytest

from sassie_qt.modules.base import SassieModuleRunner
from sassie_qt.modules.build_utilities.runner import BuildUtilitiesRunner
from sassie_qt.modules.eros.runner import ErosRunner
from sassie_qt.modules.merge_utilities.runner import MergeUtilitiesRunner
from sassie_qt.modules.openmm.runner import OpenMMRunner


MODULE_DATA = Path(__file__).resolve().parents[1] / "sassie_qt" / "modules"


class _NoOpSassieModule:
    def main(self, variables, txt_queue):
        txt_queue.put("STATUS 1.0\n")


class _SecurityProbeRunner(SassieModuleRunner):
    module = "security_probe"
    variable_types = {"run_name": "string"}

    def form_to_svariables(
        self,
        project_directory: Path,
        form_values: dict[str, str],
    ) -> dict[str, str]:
        return {"run_name": form_values["run_name"]}

    def validate_variables(self, variables: dict, project_directory: Path) -> None:
        return None

    def create_sassie_module(self):
        return _NoOpSassieModule()


def test_run_name_path_traversal_is_rejected_before_cleanup(tmp_path):
    project_directory = tmp_path / "project"
    escaped_run_path = tmp_path / "escape" / "security_probe"
    escaped_run_path.mkdir(parents=True)
    sentinel = escaped_run_path / "sentinel.txt"
    sentinel.write_text("do not delete", encoding="utf-8")

    with pytest.raises(ValueError, match="Run names may contain only"):
        _SecurityProbeRunner().run(project_directory, {"run_name": "../escape"})

    assert sentinel.exists()


@pytest.mark.parametrize(
    "bad_output_name",
    [
        "../outside.pdb",
        "/tmp/outside.pdb",
    ],
)
def test_build_utilities_rejects_unsafe_output_filenames(tmp_path, bad_output_name):
    local_data = MODULE_DATA / "build_utilities" / "local_data"

    with pytest.raises(ValueError, match="output filename"):
        BuildUtilitiesRunner().prepare_variables(
            tmp_path,
            {
                "run_name": "run_0",
                "build_utilities_listbox": "c1",
                "input_pdbfile": str(local_data / "hiv1_gag.pdb"),
                "pdb_choices_listbox": "c4",
                "translation_rotation_output_filename": bad_output_name,
            },
        )


@pytest.mark.parametrize(
    "bad_output_name",
    [
        "../outside.dcd",
        "/tmp/outside.dcd",
    ],
)
def test_merge_utilities_rejects_unsafe_output_filenames(tmp_path, bad_output_name):
    local_data = MODULE_DATA / "merge_utilities" / "local_data"

    with pytest.raises(ValueError, match="output filename"):
        MergeUtilitiesRunner().prepare_variables(
            tmp_path,
            {
                "runname": "run_0",
                "trajectory_checkbox": "true",
                "sas_checkbox": "false",
                "number_of_runs_to_merge": "2",
                "pdb_file": str(local_data / "hiv1_gag.pdb"),
                "trajectory_names": ",".join(
                    [
                        str(local_data / "run_m1.dcd"),
                        str(local_data / "run_m2.dcd"),
                    ]
                ),
                "output_filename": bad_output_name,
            },
        )


@pytest.mark.parametrize(
    "bad_output_name",
    [
        "../outside.dcd",
        "/tmp/outside.dcd",
    ],
)
def test_openmm_rejects_unsafe_output_filenames(tmp_path, bad_output_name):
    local_data = MODULE_DATA / "openmm" / "local_data"

    with pytest.raises(ValueError, match="output DCD"):
        OpenMMRunner().prepare_variables(
            tmp_path,
            {
                "runname": "run_0",
                "pdbfile": str(local_data / "ssdna.pdb"),
                "infile": str(local_data / "ssdna.pdb"),
                "psffile": str(local_data / "ssdna.psf"),
                "outfile": bad_output_name,
            },
        )


@pytest.mark.parametrize("member_type", [tarfile.SYMTYPE, tarfile.LNKTYPE])
def test_eros_archive_rejects_link_members(tmp_path, member_type):
    archive_path = tmp_path / "profiles.tar"
    with tarfile.open(archive_path, "w") as archive:
        member = tarfile.TarInfo("spectra/bad_link")
        member.type = member_type
        member.linkname = "../../outside"
        archive.addfile(member)

    with tarfile.open(archive_path) as archive:
        with pytest.raises(ValueError, match="Archive links are not supported"):
            ErosRunner()._extract_archive_safely(archive, tmp_path / "extract")
