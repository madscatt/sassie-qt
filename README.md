# sassie-qt

Qt interface for SASSIE.

This repository will hold the desktop Qt version of SASSIE, including the user
interface code, application wiring, and supporting project documentation.

## Status

The first navigation prototype is available. It reads the canonical
`genapp_zazzie/menu.json`, shows the SASSIE menu groups, and opens module tabs
for the selected group: Tools, Build, Contrast, Simulate, Calculate, Analyze,
Admin, and File Manager.

The prototype loads GenApp module JSON field metadata and resolves matching
`gui_mimic_*` files from the local `zazzie` source tree. Most modules are still
native Qt stubs, while `data_interpolation` is wired to the local SASSIE module
through a gui_mimic-style runner.

Files chosen through local file inputs are copied into the app-level project
directory before a module runs. This mirrors the GenApp server model in a
desktop-friendly way: SASSIE receives project-local file paths, and outputs are
written under the selected project directory.

## Development

Project tooling and build instructions will be added as the Qt implementation
takes shape.

Run the prototype with the project Anaconda Python:

```bash
/Users/curtisj/anaconda3/bin/python run_sassie_qt.py
```

Optional source roots can be overridden:

```bash
/Users/curtisj/anaconda3/bin/python run_sassie_qt.py \
  --genapp-zazzie-root /Users/curtisj/git_working_copies/genapp_zazzie \
  --zazzie-root /Users/curtisj/git_working_copies/zazzie
```
