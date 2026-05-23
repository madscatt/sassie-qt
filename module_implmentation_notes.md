# SASSIE Qt Module Implementation Notes

These notes summarize what we learned while turning `data_interpolation` from a
prototype tab into a locally runnable SASSIE Qt module. Use this as the starting
pattern for the next module implementations.

## Current Architecture

The app is still driven by the canonical GenApp metadata, but jobs run locally.

- `sassie_qt/menu_loader.py` reads `genapp_zazzie/menu.json` and each
  `genapp_zazzie/modules/<module>.json`.
- `ModuleStubPage` in `sassie_qt/prototype_app.py` builds the Qt tabs and field
  rows from that metadata.
- `JsonFieldRow` converts GenApp field types into Qt controls.
- Module-specific execution is currently explicit for `data_interpolation`.
- `sassie_qt/runners/data_interpolation_runner.py` is the local bridge into the
  SASSIE module.
- `sassie_qt/plotting/data_interpolation_plot.py` keeps Plotly export separate
  from the embedded PyQtGraph display.

The long-term pattern should be: generic JSON-driven UI, plus one small runner
and any specialized output/plot/view widgets per runnable SASSIE module.

## Metadata And UI

Fields come from the GenApp module JSON. For each field, we currently retain:

- `id`
- `label`
- `type`
- `role`
- `default`
- `values`
- `required`
- `help`

The `help` strings are normalized for Qt tooltips: GenApp `<br>` becomes a
newline, simple HTML tags are stripped, and HTML entities are unescaped. Tooltips
are applied to rows, labels, controls, Browse buttons, output placeholders, and
plot widgets.

For file inputs, GenApp `lrfile` should be treated as a local file picker in the
desktop app. Selected files are copied into the current project directory. The
last source directory is remembered per module field, so repeated browsing starts
near the user's previous selection. If no remembered source exists, browsing
starts in the project directory.

## Project Directory

The app-level project directory replaces the GenApp server upload area. The
default is:

```text
no_project_specified
```

This matches the SASSIE-web default name. The app creates the folder if it does
not exist. Module runs use:

```text
<project_directory>/<run_name>/<module_name>/
```

For `data_interpolation`, the SASSIE module writes into:

```text
<project_directory>/<run_name>/data_interpolation/
```

## Runner Pattern

`DataInterpolationRunner` follows the old `gui_mimic`/bin-driver flavor without
GenApp server overhead.

Important pieces:

1. Collect strings and paths from the Qt form.
2. Validate local desktop path mistakes before calling SASSIE filters.
3. Build `svariables`, matching the SASSIE input names and type strings.
4. Call `sassie.interface.input_filter.type_check_and_convert`.
5. Call the module-specific SASSIE filter, here
   `data_interpolation_filter.check_data_interpolation`.
6. Create/clean the module run directory.
7. Run the SASSIE module in a background process.
8. Drain the SASSIE text queue.
9. Convert `STATUS <fraction>` queue messages into progress updates.
10. Send all other queue messages to the Qt run log.
11. Return a result object with the expected output files.

Running in a background `QThread` keeps the GUI responsive. The SASSIE work itself
is still launched in a `multiprocessing.Process`, matching the queue-based SASSIE
module API.

## Data Interpolation Inputs

The Qt module collects:

- `run_directory`: app-level project directory
- `run_name`
- `data_file_name`
- `output_file_name`
- `izero`
- `izero_error`
- `delta_q`
- `maximum_points`

The runner converts these to SASSIE variables:

```python
{
    "run_name": (run_name, "string"),
    "data_file_name": (data_file_name, "string"),
    "output_file_name": (output_file_name, "string"),
    "izero": (izero, "float"),
    "izero_error": (izero_error, "float"),
    "delta_q": (delta_q, "float"),
    "maximum_points": (maximum_points, "int"),
}
```

This is the key bridge to copy for the next modules: use the same SASSIE variable
names and type strings that the `gui_mimic_*` file uses.

## Output, Errors, And Progress

The output tab includes:

- An embedded progress bar with the percentage text centered inside the bar.
- A run log text area.
- Modal error popups for validation failures and failed SASSIE runs.

The GenApp `progress_html` field is ignored in the Qt UI because the progress bar
already carries the percentage. The run log is important because many SASSIE
modules report meaningful status through the queue instead of structured events.

When the child process exits nonzero, the runner includes the recent queue log in
the error text. This is much more useful than only showing the process exit code.

## Plotting

For the embedded plot, we chose PyQtGraph instead of embedded Plotly/JavaScript.
This keeps the Qt app responsive and avoids browser-engine overhead.

The data interpolation plot widget provides:

- Embedded PyQtGraph plot.
- Pan mode.
- Box Zoom mode for drag-selecting an x/y region.
- Mouse wheel zoom.
- Axis-only zoom by dragging an axis.
- Reset View.
- Save PNG.
- Export Plotly HTML.
- Open Plotly in the system browser.

Plotly remains useful for a richer browser view and for sharing/export. We write
a self-contained HTML file beside the module outputs. The Plotly JavaScript comes
from the installed Python `plotly` package, not a CDN.

For PyQtGraph log plots, a few manual fixes were needed:

- Disable automatic SI-prefix rewriting so inverse Angstrom does not become
  misleading text such as `mA^-1`.
- Label the x-axis as `q (1/Å)`.
- Use sparse log tick labels for q to prevent overlap.
- Do not use microscopic placeholder values for invalid error-bar bottoms.
  Negative or zero error-bar lows poison the log range.
- Compute the default view range from meaningful positive data and positive error
  bounds.
- Clip nonpositive error-bar bottoms to the visible plot floor.

## Module-Specific Plot Data

`data_interpolation` writes a JSON plot file:

```text
<run_path>/<output_file_stem>.json
```

The embedded PyQtGraph plot and the Plotly export both read that JSON. The JSON
contains original data, interpolated data, error arrays, and the S/N cutoff.

For future modules, prefer a small module-specific plotting helper that converts
the SASSIE output format into:

- a native Qt/PyQtGraph view for the app
- an optional Plotly figure for export/open-in-browser

Keep those concerns separate from the runner.

## UI Lessons

- Keep GenApp field type badges and required badges out of the UI; they were too
  noisy for desktop use.
- Keep OpenGL tabs by default for prototype modules, but remove them for modules
  that clearly do not need them, such as `data_interpolation`.
- Keep the output tab focused. For `data_interpolation`, the run log can own most
  of the output area.
- Hover tooltips work, but can feel inconsistent on macOS until the window is
  active and the mouse rests over an actual tooltip-bearing widget.
- Visible help buttons were too busy, so tooltips remain the current mechanism.
- PyQtGraph does not do Plotly-level automatic tick layout. Add custom tick
  formatting where readability matters.

## Checklist For The Next Working Module

1. Read the module JSON in `genapp_zazzie/modules/<module>.json`.
2. Read the matching `gui_mimic_<module>.py` in `zazzie/src/sassie/...`.
3. Identify the exact SASSIE variable names and type strings.
4. Create a module input dataclass.
5. Create a module result dataclass.
6. Create a runner in `sassie_qt/runners/`.
7. Validate desktop-only issues first: missing files, directories where files are
   expected, missing run name, missing output names.
8. Use `input_filter.type_check_and_convert`.
9. Use the module-specific SASSIE filter.
10. Run the SASSIE module off the GUI thread.
11. Drain queue messages into the run log.
12. Convert `STATUS` messages into progress updates.
13. Surface failures both in the run log and as modal dialogs.
14. Identify module outputs and return them in the result dataclass.
15. Add any output widgets: text, file summaries, plots, molecular views, images.
16. Add focused tests for input collection, validation, runner behavior, output
   wiring, and UI state.

## Testing Pattern

Current tests cover:

- canonical menu loading
- module JSON loading
- tooltip normalization
- project directory default and creation
- file-copy behavior into the project directory
- remembered file browsing directories
- data interpolation input collection
- progress bar updates
- runner validation and failure messages
- plot loading
- Plotly HTML export
- PyQtGraph PNG export
- log-axis range and sparse tick behavior

For every new module, add runner tests and one or two UI wiring tests before
connecting it to the real SASSIE code. This keeps the prototype from becoming a
large manual-click test surface.
