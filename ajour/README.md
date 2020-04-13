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

## Running

Setting up:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
# Install our patched version of pandas_access.
(cd pandas_access && pip install -e .)
```

Running:

```bash
ajour
```
