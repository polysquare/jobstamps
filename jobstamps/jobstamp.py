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

from collections import namedtuple


def _safe_mkdir(directory):
    """Create a directory, ignoring errors if it already exists."""
    try:
        os.makedirs(directory)
    except OSError as error:
        if error.errno != errno.EEXIST:
            raise error


def _stamp(stampfile, func, *args, **kwargs):
    """Store the repr() of the return value of func in stampfile."""
    value = func(*args, **kwargs)
    with open(stampfile, "wb") as stamp:
        stamp.truncate()
        pickle.dump(value, stamp)

    return value


def _stamp_and_update_hook(method,  # suppress(too-many-arguments)
                           dependencies,
                           stampfile,
                           func,
                           *args,
                           **kwargs):
    """Write stamp and call update_stampfile_hook on method."""
    result = _stamp(stampfile, func, *args, **kwargs)
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

_JOBSTAMPS_KWARGS_DESCRIPTIONS = """
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


_OutOfDateActionDetail = namedtuple("_OutOfDateActionDetail",
                                    "stamp dependencies method kwargs")


def _out_of_date(func, *args, **kwargs):
    """Internal function returning out of date file and detail to run job."""
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

    detail = _OutOfDateActionDetail(stamp=stamp_file_name,
                                    dependencies=dependencies,
                                    method=method_class(stamp_file_name),
                                    kwargs=kwargs)

    if not os.path.exists(stamp_file_name):
        return stamp_file_name, detail

    for expected_output_file in expected_output_files:
        if not os.path.exists(expected_output_file):
            return expected_output_file, detail

    for dependency in dependencies:
        if (not os.path.exists(dependency) or
                not detail.method.check_dependency(dependency)):
            return dependency, detail

    return None, detail


def out_of_date(func, *args, **kwargs):  # suppress(unused-function)
    """Return relevant file in the job's proposed call that is out of date.

    If nothing is out of date, return None.

    This method can be used to check if func will run, without actually
    running it.

    {kwargs_description}
    """.format(kwargs_description=_JOBSTAMPS_KWARGS_DESCRIPTIONS)
    return _out_of_date(func, *args, **kwargs)[0]


def run(func, *args, **kwargs):
    """Run a job, re-using the cached result if not out of date.

    {kwargs_description}
    """.format(kwargs_description=_JOBSTAMPS_KWARGS_DESCRIPTIONS)
    trigger, detail = _out_of_date(func, *args, **kwargs)
    jobstamps_debug = os.environ.get("JOBSTAMPS_DEBUG", None)

    if trigger:
        if jobstamps_debug:
            print("""JOBSTAMP: Dependency {0} out of """  # pragma: no cover
                  """date, re-running {1}""".format(trigger,
                                                    func.__name__))

        return _stamp_and_update_hook(detail.method,
                                      detail.dependencies,
                                      detail.stamp,
                                      func,
                                      *args,
                                      **detail.kwargs)

    # It is safe to re-use the cached value, open the stampfile
    # and return its contents
    if jobstamps_debug:
        print("""JOBSTAMP: Dependencies up to date, """  # pragma: no cover
              """using cached value of {} from {}""".format(func.__name__,
                                                            detail.stamp))

    with open(detail.stamp, "rb") as stamp:
        return pickle.load(stamp)
