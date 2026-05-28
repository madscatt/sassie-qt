# AGENTS.md

## Local Development Machine

- Model: MacBook Pro
- Display size: 16-inch
- Release date: November 2023
- Chip: Apple M3 Max
- Memory: 64 GB
- Startup disk: Macintosh HD
- macOS: Tahoe 26.4.1

Do not store or expose the machine serial number in this repository.

## Related Repositories

Agents working in this repository may use the following repositories as
read-only references, or copy from them as needed:

- `madscatt/zazzie`
- `madscatt/zazmol`
- `ehb54/zazzie`, referred to locally as `genapp_zazzie`
- `ehb54/genapp`

These repositories are available under `~/git_working_copies`.

`zazzie` is a temporary name for the development version of SASSIE, and
`zazmol` is a temporary name for the development version of SASMOL. The old
SASSIE project is being retired. As this project moves forward, repository and
package names may change from `z*` names back to `s*` names.

## Python Environment

Use the Python installation under `~/anaconda3`. The `sasmol` and `sassie`
packages are installed there.

Use PySide6 for Qt development in this repository. Do not mix PySide6 with
PyQt bindings in the same application.

## Molecular Viewer Renderer Guidance

For the desktop molecular viewer, prefer VTK/PyVistaQt as the primary renderer
unless a product requirement explicitly demands native Metal/Direct3D/Vulkan
alignment through Qt RHI. VTK is the lower-risk molecular visualization path
because it already provides mature scientific rendering, Qt integration, and
cross-platform GPU display support.

Use Qt Quick 3D / Qt RHI as an evaluation or secondary renderer path when
platform-native graphics abstraction is a hard requirement, but expect more
custom molecular-visualization work for bonds, ribbons, surfaces, picking,
selection, and specialized representations.

Local prototype timing notes are intentionally untracked scratch files unless
they are promoted into tracked documentation. If present, they can be useful as
rough renderer references:

- `PyVistaQt_VTK_renderer_timings.md`: PyVistaQt/VTK point-cloud rendering
  handled the 6,730-atom HIV Gag trajectory at about 113 coordinate updates/s.
- `QtQuick3D_RHI_renderer_timings.md`: Qt Quick 3D / Qt RHI with Metal and
  sphere instancing handled the same trajectory at about 59 displayed
  updates/s, apparently vsync/display-cadence limited.

For either renderer, decouple simulation from display. Accept coordinates as
fast as the simulation engine produces them, keep the latest displayable frame
for interactive viewing, and render on a fixed 30 or 60 Hz GUI cadence so the
renderer does not back-pressure simulation.

## Coding Style

- Prefer snake_case for class and method names, such as `name_of_function`,
  instead of PascalCase names such as `NameOfFunction`.
- Prefer self-defining variable names. For example, use `number_of_atoms`
  instead of abbreviated names such as `natoms`.
