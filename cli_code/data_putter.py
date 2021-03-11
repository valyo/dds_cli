"""Data putter."""

###############################################################################
# IMPORTS ########################################################### IMPORTS #
###############################################################################

# Standard library
import logging
import pathlib
import sys
import traceback
import os

# Installed
import botocore
import requests
import rich

# Own modules
from cli_code import base
from cli_code import file_handler_local as fhl
from cli_code import s3_connector as s3
from cli_code import DDSEndpoint
from cli_code.cli_decorators import verify_proceed, update_status

###############################################################################
# START LOGGING CONFIG ################################# START LOGGING CONFIG #
###############################################################################

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)

###############################################################################
# CLASSES ########################################################### CLASSES #
###############################################################################


class DataPutter(base.DDSBaseClass):
    """Data putter class."""

    def __init__(
        self,
        username: str = None,
        config: pathlib.Path = None,
        project: str = None,
        break_on_fail: bool = False,
        overwrite: bool = False,
        source: tuple = (),
        source_path_file: pathlib.Path = None,
    ):

        # Initiate DDSBaseClass to authenticate user
        super().__init__(username=username, config=config, project=project)

        # Initiate DataPutter specific attributes
        self.break_on_fail = break_on_fail
        self.overwrite = overwrite
        self.filehandler = None
        self.status = dict()

        # Only method "put" can use the DataPutter class
        if self.method != "put":
            sys.exit(f"Unauthorized method: {self.method}")

        # Get file info
        self.filehandler = fhl.LocalFileHandler(user_input=(source, source_path_file))
        self.verify_bucket_exist()
        files_in_db = self.filehandler.check_previous_upload(token=self.token)

        # Quit if error and flag
        if files_in_db and self.break_on_fail and not self.overwrite:
            sys.exit(
                "Some files have already been uploaded and "
                f"'--break-on-fail' flag used. \n\nFiles: {files_in_db}"
            )

        # Generate status dict
        self.status = self.filehandler.create_upload_status_dict(
            existing_files=files_in_db, overwrite=self.overwrite
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        if exc_type is not None:
            traceback.print_exception(exc_type, exc_value, tb)
            return False  # uncomment to pass exception through

        return True

    # General methods ###################### General methods #
    @verify_proceed
    @update_status
    def put(self, file):
        """Uploads files to the cloud."""

        uploaded = False
        error = ""
        file_local = str(self.filehandler.data[file]["path_local"])
        file_remote = self.filehandler.data[file]["name_in_bucket"]

        with s3.S3Connector(project_id=self.project, token=self.token) as conn:

            if None in [conn.url, conn.keys, conn.bucketname]:
                error = "No s3 info returned! " + conn.message
            else:
                # Upload file
                try:
                    conn.resource.meta.client.upload_file(
                        Filename=file_local,
                        Bucket=conn.bucketname,
                        Key=file_remote,
                        ExtraArgs={
                            "ACL": "private",  # Access control list
                            "CacheControl": "no-store",  # Don't store cache
                        },
                    )
                except botocore.client.ClientError as err:
                    error = f"S3 upload of file '{file}' failed: {err}"
                    LOG.exception("%s: %s", file, err)
                else:
                    uploaded = True

        return uploaded, error

    @verify_proceed
    @update_status
    def add_file_db(self, file):
        """Make API request to add file to DB."""

        added_to_db = False
        error = ""

        # Get file info
        fileinfo = self.filehandler.data[file]
        params = {
            "name": file,
            "name_in_bucket": fileinfo["name_in_bucket"],
            "subpath": fileinfo["subpath"],
            "size": fileinfo["size"],
        }
        # Send file info to API
        put_or_post = requests.put if fileinfo["overwrite"] else requests.post
        response = put_or_post(
            DDSEndpoint.FILE_NEW,
            params=params,
            headers=self.token,
        )

        # Error if failed
        if not response.ok:
            error = f"Failed to add file '{file}' to database: {response.text}"
            LOG.exception(error)
            return added_to_db, error

        added_to_db, error = (True, response.json()["message"])

        return added_to_db, error
