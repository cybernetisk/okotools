import os
import tarfile
import tempfile
from pathlib import Path


def human_readable_size(size: int, decimal_places: int = 2):
    dec = 0
    for unit in ["B", "KiB", "MiB", "GiB", "TiB"]:
        if size < 1024.0:
            break
        size /= 1024.0
        dec = decimal_places
    return f"{size:.{dec}f}{unit}"


def create_archive() -> str:
    fd, output_file = tempfile.mkstemp(prefix="cyboko_", suffix=".tgz")
    os.close(fd)

    src_dir = Path("C:\\Ajour")
    src_files = [
        src_dir / "Cashdata.mdb",
        src_dir / "ModulerX.mdb",
        src_dir / "Cashregn.mdb",
        src_dir / "Knapdata.mdb",
        src_dir / "DataFlet.mdb",
    ]

    with tarfile.open(output_file, "w:gz") as tar:
        for file in src_files:
            tar.add(file, arcname=file.relative_to(src_dir))

    return output_file


def main():
    output_file = create_archive()

    print(
        "Compressed size: {}".format(human_readable_size(os.path.getsize(output_file)))
    )

    # os.remove(output_file)


if __name__ == "__main__":
    main()
