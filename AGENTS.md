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

## Coding Style

- Prefer snake_case for class and method names, such as `name_of_function`,
  instead of PascalCase names such as `NameOfFunction`.
- Prefer self-defining variable names. For example, use `number_of_atoms`
  instead of abbreviated names such as `natoms`.
