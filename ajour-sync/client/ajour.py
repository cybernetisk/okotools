import os
import sys
import tarfile
import tempfile
import urllib.request
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


def upload(arc_file):
    # Not very memory efficient, but want to stick to built-in libraries.
    # The compressed tgz file is about 29 MiB as of 2020-01-03.
    data = Path(arc_file).read_bytes()
    req = urllib.request.Request(
        url="https://ajour-sync.cyb.no/archive",
        data=data,
        method="PUT",
        headers={"Content-Type": "application/gzip"},
    )
    with urllib.request.urlopen(req) as f:
        pass

    if f.status != 201:
        print("Unexpected status: {} ({})".format(f.status, f.reason))


def sync():
    print("Creating archive")
    output_file = create_archive()

    print(
        "Compressed size: {}".format(human_readable_size(os.path.getsize(output_file)))
    )

    print("Will now upload")

    upload(output_file)
    print("Upload complete")

    # os.remove(output_file)


def self_update():
    print("Self-updating")
    url = "https://raw.githubusercontent.com/cybernetisk/okotools/ajour-sync/ajour-sync/client/ajour.py"

    response = urllib.request.urlopen(url)
    data = response.read().decode("utf-8")

    with open(__file__, "w") as f:
        f.write(data)


def usage():
    print("Unknown command")
    sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        usage()

    command = sys.argv[1]
    if command == "self-update":
        self_update()
    elif command == "sync":
        sync()
    else:
        usage()
