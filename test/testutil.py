# /test/testutil.py
#
# Common functions for jobstamps tests.
#
# See /LICENCE.md for Copyright information
"""Common functions for jobstamps tests."""

import os

import shutil

import sys

import tempfile

from six import StringIO

import testtools


class CapturedOutput(object):  # suppress(too-few-public-methods)

    """Represents the captured contents of stdout and stderr."""

    def __init__(self):
        """Initialize the class."""
        super(CapturedOutput, self).__init__()
        self.stdout = ""
        self.stderr = ""

        self._stdout_handle = None
        self._stderr_handle = None

    def __enter__(self):
        """Start capturing output."""
        self._stdout_handle = sys.stdout
        self._stderr_handle = sys.stderr

        sys.stdout = StringIO()
        sys.stderr = StringIO()

        return self

    def __exit__(self, exc_type, value, traceback):
        """Finish capturing output."""
        del exc_type
        del value
        del traceback

        sys.stdout.seek(0)
        self.stdout = sys.stdout.read()

        sys.stderr.seek(0)
        self.stderr = sys.stderr.read()

        sys.stdout = self._stdout_handle
        self._stdout_handle = None

        sys.stderr = self._stderr_handle
        self._stderr_handle = None


class InTemporaryDirectoryTestBase(testtools.TestCase):

    """A TestCase which happens inside a temporary directory."""

    def __init__(self, *args, **kwargs):
        """Initialize instance variables."""
        super(InTemporaryDirectoryTestBase, self).__init__(*args, **kwargs)
        self._temporary_directory = None

    def setUp(self):  # suppress(N802)
        """Set up this TestCase and create directory, changing into it."""
        self._temporary_directory = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(self._temporary_directory))
        current_directory = os.getcwd()
        os.chdir(self._temporary_directory)
        self.addCleanup(lambda: os.chdir(current_directory))

        super(InTemporaryDirectoryTestBase, self).setUp()
