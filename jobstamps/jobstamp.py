# /jobstamps/jobstamp.py
#
# Main module for jobstamps.
#
# See /LICENCE.md for Copyright information
"""Main module for jobstamps."""

import errno

import hashlib

import json

import os

import pickle

import tempfile


def _safe_mkdir(directory):
    """Create a directory, ignoring errors if it already exists."""
    try:
        os.makedirs(directory)
    except OSError as error:
        if error.errno != errno.EEXIST:
            raise error


def _stamp(stampfile, trigger, func, *args, **kwargs):
    """Store the repr() of the return value of func in stampfile."""
    if os.environ.get("JOBSTAMPS_DEBUG", None):
        print("""JOBSTAMP: Dependency {0} out of date, """  # pragma: no cover
              """re-running {1}""".format(trigger,
                                          func.__name__))
    value = func(*args, **kwargs)
    with open(stampfile, "wb") as stamp:
        stamp.truncate()
        pickle.dump(value, stamp)

    return value


def _stamp_and_update_hook(method,  # suppress(too-many-arguments)
                           dependencies,
                           stampfile,
                           trigger,
                           func,
                           *args,
                           **kwargs):
    """Write stamp and call update_stampfile_hook on method."""
    result = _stamp(stampfile, trigger, func, *args, **kwargs)
    method.update_stampfile_hook(dependencies)
    return result


def _sha1_for_file(filename):
    """Return sha1 for contents of filename."""
    with open(filename, "rb") as fileobj:
        contents = fileobj.read()
        return hashlib.sha1(contents).hexdigest()


class MTimeMethod(object):

    """Method to verify if dependencies are up to date using timestamps."""

    def __init__(self, stamp_file_path):
        """Initialize and store mtime of stamp_file_path."""
        super(MTimeMethod, self).__init__()
        if os.path.exists(stamp_file_path):
            self._stamp_file_mtime = os.path.getmtime(stamp_file_path)
        else:
            self._stamp_file_mtime = 0

    def check_dependency(self, dependency_path):
        """Check if mtime of dependency_path is greater than stored mtime."""
        return os.path.getmtime(dependency_path) <= self._stamp_file_mtime

    def update_stampfile_hook(self, dependencies):  # suppress(no-self-use)
        """Perform nothing."""
        del dependencies


class HashMethod(object):

    """Method to verify if dependencies are up to date using a hash."""

    def __init__(self, stamp_file_path):
        """Initialize and store filenames for hash files."""
        super(HashMethod, self).__init__()
        self._stamp_file_hashes_path = "{}.dep.sha1".format(stamp_file_path)

        if os.path.exists(self._stamp_file_hashes_path):
            with open(self._stamp_file_hashes_path, "r") as hashes_file:
                hashes_contents = hashes_file.read()
                self._stamp_file_hashes = json.loads(hashes_contents)
        else:
            self._stamp_file_hashes = dict()

    def check_dependency(self, dependency_path):
        """Check if mtime of dependency_path is greater than stored mtime."""
        stored_hash = self._stamp_file_hashes.get(dependency_path)

        # This file was newly added, or we don't have a file
        # with stored hashes yet. Assume out of date.
        if not stored_hash:
            return False

        return stored_hash == _sha1_for_file(dependency_path)

    def update_stampfile_hook(self, dependencies):  # suppress(no-self-use)
        """Loop over all dependencies and store hash for each of them."""
        hashes = {d: _sha1_for_file(d) for d in dependencies
                  if os.path.exists(d)}
        with open(self._stamp_file_hashes_path, "wb") as hashes_file:
            hashes_file.write(json.dumps(hashes).encode("utf-8"))


def _determine_method(user_method):
    """Return class representing default dependency-change-detection method.

    This will be MTimeMethod in most cases, except where the
    JOBSTAMPS_ALWAYS_USE_HASHES environment variable is set, in which
    case it will always be HashMethod.
    """
    if os.environ.get("JOBSTAMPS_ALWAYS_USE_HASHES", None):
        return HashMethod  # pragma: no cover
    else:
        return user_method or MTimeMethod


def run(func, *args, **kwargs):
    """Run a job, re-using the cached result if not out of date.

    :jobstamps_dependencies: If the stamp file is newer than any file in this
                             list, re-run the job.
    :jobstamps_output_files: If any of the files in this list do not
                             exist, run-run the job.
    :jobstamps_cache_output_directory: Directory to store stamp-files, default
                                       will be 'TMPDIR/jobstamps'.
    :jobstamps_method: Method used to determine if dependencies are out of
                       date. By default, MTimeMethod is used, but HashMethod
                       should be used if files are being copied around
                       without being changed substantively.
    """
    storage_directory = os.path.join(tempfile.gettempdir(), "jobstamps")
    stamp_input = "".join([func.__name__] +
                          [repr(v) for v in args] +
                          [repr(kwargs[k])
                           for k in sorted(kwargs.keys())]).encode("utf-8")

    dependencies = kwargs.pop("jobstamps_dependencies", None) or list()
    expected_output_files = (kwargs.pop("jobstamps_output_files", None) or
                             list())
    cache_output_directory = kwargs.pop("jobstamps_cache_output_directory",
                                        None) or storage_directory
    method_class = _determine_method(kwargs.pop("jobstamps_method", None))

    stamp_file_name = os.path.join(cache_output_directory,
                                   hashlib.md5(stamp_input).hexdigest())
    _safe_mkdir(cache_output_directory)

    if not os.path.isdir(cache_output_directory):
        raise IOError("""{} exists and is """
                      """not a directory.""".format(cache_output_directory))

    method = method_class(stamp_file_name)

    if not os.path.exists(stamp_file_name):
        return _stamp_and_update_hook(method,
                                      dependencies,
                                      stamp_file_name,
                                      stamp_file_name,
                                      func,
                                      *args,
                                      **kwargs)

    for expected_output_file in expected_output_files:
        if not os.path.exists(expected_output_file):
            return _stamp_and_update_hook(method,
                                          dependencies,
                                          stamp_file_name,
                                          expected_output_file,
                                          func,
                                          *args,
                                          **kwargs)

    for dependency in dependencies:
        if (not os.path.exists(dependency) or
                not method.check_dependency(dependency)):
            return _stamp_and_update_hook(method,
                                          dependencies,
                                          stamp_file_name,
                                          dependency,
                                          func,
                                          *args,
                                          **kwargs)

    # It is safe to re-use the cached value, open the stampfile
    # and return its contents
    if os.environ.get("JOBSTAMPS_DEBUG", None):
        print("""JOBSTAMP: Dependencies up to date, """  # pragma: no cover
              """using cached value of {} from {}""".format(func.__name__,
                                                            stamp_file_name))

    with open(stamp_file_name, "rb") as stamp:
        return pickle.load(stamp)
