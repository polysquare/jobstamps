# /test/testutil.py
#
# Common functions for jobstamps tests.
#
# See /LICENCE.md for Copyright information
"""Common functions for jobstamps tests."""

import os

import shutil

import tempfile

import testtools


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


def temporarily_clear_variable_on_testsuite(suite, variable):
    """Temporarily clear environment variable on suite."""
    if os.environ.get(variable, None):
        original = {
            variable: os.environ[variable]
        }
        del os.environ[variable]
        suite.addCleanup(lambda: os.environ.update(original))
