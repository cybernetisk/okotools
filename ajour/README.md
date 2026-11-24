# cyb ajour

## Requirements

* MDB Tools: https://github.com/brianb/mdbtools
  * On Arch, this can be installed by

    ```bash
    yay -S mdbtools
    ```

* Patched version of pandas_access: https://github.com/cybernetisk/pandas_access
  * We use Git submodules to keep a reference from this repo.

    ```bash
    git submodule update --init
    ```

## Getting latest data

You need keys to the server. See script.

```bash
./fetch-latest-data.sh
```

## Running

Install [uv](https://docs.astral.sh/uv/). It installs the patched pandas_access from the submodule.

```bash
uv run ajour
```
