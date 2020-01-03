import logging
import os
import shutil
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, escape, request, Response

storage_dir = Path(os.getenv("STORAGE_DIR"))

app = Flask(__name__)

app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.INFO)


def text_response(value, status):
    return Response(value, mimetype='text/plain', status=status)


@app.route("/archive", methods=["PUT"])
def upload_rpm():
    if request.content_length is None or request.content_length == 0:
        return text_response("Missing contents\n", 400)

    if request.content_type != "application/gzip":
        return text_response("Expected content type of application/gzip\n", 400)

    tmp_fd, tmp_path = tempfile.mkstemp()
    os.close(tmp_fd)
    with open(tmp_path, "wb") as f:
        f.write(request.stream.read())

    # Verify the tarfile can be read.
    with tarfile.open(tmp_path, "r:gz") as tar:
        app.logger.info("Contents of tarfile")
        for name in tar.getnames():
            app.logger.info("- " + name)

    now = datetime.now().replace(tzinfo=timezone.utc)
    target_path = storage_dir / "{}.tgz".format(now.strftime("%Y%m%d-%H%M%SZ.tgz"))

    app.logger.info("Storing to {}".format(target_path))

    shutil.move(tmp_path, target_path)
    os.remove(tmp_path)

    return text_response("Created\n", 201)


@app.route("/")
def hello():
    return f"https://github.com/cybernetisk/okotools"
