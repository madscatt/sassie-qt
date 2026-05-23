# SASSIE-web Layout Summary

SASSIE-web is a GenApp wrapper around SASSIE, not the scientific core itself.
The active web boundary is:

```text
menu.json
  -> modules/<module>.json
    -> bin/<module> driver
      -> sassie.interface.input_filter
      -> sassie.interface.<module>.<module>_filter
      -> sassie.<area>.<module>.<module>.main(...)
```

## Application Navigation

The top-level web navigation comes from
`/Users/curtisj/git_working_copies/genapp_zazzie/menu.json`. It groups modules
into Tools, Build, Contrast, Simulate, Calculate, Analyze, Admin, and
etc/File Manager.

In the live app at `http://localhost:8080/sassie3/`, those groups appear as the
dark left-side category menu with icons. Choosing a category opens a horizontal
module tab row. For example, Tools opens Align, Data Interpolation, Extract
Utilities, and Merge Utilities.

## Module JSON Layout

Each `modules/*.json` file defines the GUI form:

- field ids
- labels
- defaults
- field types
- required flags
- help text
- role, usually `input` or `output`
- layout placement

Common panels include `root`, `header`, `body`, `inputpanel`, `msgspanel`,
`resultpanel`, and `footer`. Fields attach to panels with `layout.parent`.

Dynamic or conditional UI is represented through `repeater` and `repeat`, for
example listbox- or checkbox-driven advanced inputs and repeated component
sections.

The web field types include `text`, `integer`, `float`, `lrfile`, `listbox`,
`checkbox`, `label`, `button`, and `integerpair`, plus output types such as
`progress`, `html`, `plotly`, and `atomicstructure`.

In the browser, these JSON definitions become forms such as the Data
Interpolation module, with run name, file upload/server browse, numeric inputs,
progress, percent text, plot area, Submit, and Reset.

## Bin-Driver Layer

The `bin/` scripts are the GenApp-facing bin-drivers. They accept GenApp JSON,
unpack uploaded files and runtime metadata such as `_base_directory`,
`_udphost`, `_udpport`, and `_uuid`, translate web field names into SASSIE
variables, run `input_filter.type_check_and_convert(...)`, and then call the
module-specific filter.

After validation, they run the core module, often in a `multiprocessing.Process`,
and stream status back through UDP using keys such as `_progress`,
`progress_output`, `progress_html`, and `_textarea`.

The bin-drivers are derived from the SASSIE `gui_mimic_*` files. For example:

- `/Users/curtisj/git_working_copies/genapp_zazzie/bin/align` mirrors
  `/Users/curtisj/git_working_copies/zazzie/src/sassie/tools/align/gui_mimic_align.py`
- `/Users/curtisj/git_working_copies/genapp_zazzie/bin/data_interpolation`
  mirrors
  `/Users/curtisj/git_working_copies/zazzie/src/sassie/tools/data_interpolation/gui_mimic_data_interpolation.py`

The `gui_mimic_*` files are a useful source of truth for SASSIE-side variable
names, defaults, imports, filters, and run order. The bin-driver adds the
web-specific layer: JSON args, uploaded-file array handling, working-directory
changes, local testing mode, UDP progress, Plotly/atomicstructure output
mapping, and final JSON response.

## Input Filtering

Input validation is layered.

`/Users/curtisj/git_working_copies/zazzie/src/sassie/interface/input_filter.py`
handles general type conversion and broad checks: strings, booleans, ints,
floats, arrays, nested arrays, file/path safety, permissions, PDB/DCD
compatibility, PSF checks, and related shared validation.

Each module then has a focused filter, such as:

- `/Users/curtisj/git_working_copies/zazzie/src/sassie/interface/align/align_filter.py`
- `/Users/curtisj/git_working_copies/zazzie/src/sassie/interface/data_interpolation/data_interpolation_filter.py`

These module filters enforce module-specific scientific and input rules before
the core module runs.

## Notes For sassie-qt

- The Qt app should probably preserve the same separation: GUI field collection,
  shared input conversion, module filter, then core module execution.
- `modules/*.json` is a good declarative inventory of current GUI fields and
  grouping, even if the Qt UI eventually becomes native widgets instead of
  GenApp panels.
- `gui_mimic_*` files are closer to the core SASSIE API contract than the web
  drivers, but the web drivers reveal practical runtime behavior, progress
  reporting, file handling, and output rendering.
- Some naming is inconsistent today, especially `runname` versus `run_name`.
  Qt should normalize carefully while staying compatible with the backend.
- Plotly and JSmol/atomicstructure are web-specific output surfaces. Qt will
  need equivalent native presentation choices for plots, text logs, progress,
  and structures.
