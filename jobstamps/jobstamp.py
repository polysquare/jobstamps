# /jobstamps/jobstamp.py
#
# Main module for jobstamps.
#
# See /LICENCE.md for Copyright information
"""Main module for jobstamps."""

import errno

import md5

import os

import tempfile

from ast import literal_eval


def _safe_mkdir(directory):
    """Create a directory, ignoring errors if it already exists."""
    try:
        os.makedirs(directory)
    except OSError as error:
        if error.errno != errno.EEXIST:
            raise error


def _stamp(stampfile, func, *args, **kwargs):
    """Store the repr() of the return value of func in stampfile."""
    if os.environ.get("JOBSTAMPS_DEBUG", None):
        print("""JOBSTAMP: Dependency out of date, """  # pragma: no cover
              """re-running {}""".format(func.__name__))
    value = func(*args, **kwargs)
    with open(stampfile, "w") as stamp:
        stamp.truncate()
        stamp.write(repr(value))

    return value


def run(func, *args, **kwargs):
    """Run a job, re-using the cached result if not out of date.

    :jobstamps_dependencies: If the stamp file is newer than any file in this
                             list, re-run the job.
    :jobstamps_output_files: If any of the files in this list do not
                             exist, run-run the job.
    :jobstamps_cache_output_directory: Directory to store stamp-files, default
                                       will be 'TMPDIR/jobstamps'
    """
    storage_directory = os.path.join(tempfile.gettempdir(), "jobstamps")
    stamp_input = "".join([func.__name__] +
                          [repr(v) for v in args] +
                          [repr(v) for v in kwargs.keys()])

    dependencies = kwargs.pop("jobstamps_dependencies", None) or list()
    expected_output_files = (kwargs.pop("jobstamps_output_files", None) or
                             list())
    cache_output_directory = kwargs.pop("jobstamps_cache_output_directory",
                                        None) or storage_directory

    stamp_file_name = os.path.join(cache_output_directory,
                                   md5.new(stamp_input).hexdigest())
    _safe_mkdir(cache_output_directory)

    if not os.path.isdir(cache_output_directory):
        raise IOError("""{} exists and is """
                      """not a directory.""".format(cache_output_directory))

    if not os.path.exists(stamp_file_name):
        return _stamp(stamp_file_name, func, *args, **kwargs)

    for expected_output_file in expected_output_files:
        if not os.path.exists(expected_output_file):
            return _stamp(stamp_file_name, func, *args, **kwargs)

    stamp_file_mtime = os.path.getmtime(stamp_file_name)

    for dependency in dependencies:
        if (not os.path.exists(dependency) or
                os.path.getmtime(dependency) > stamp_file_mtime):
            return _stamp(stamp_file_name, func, *args, **kwargs)

    # It is safe to re-use the cached value, open the stampfile
    # and return its contents
    if os.environ.get("JOBSTAMPS_DEBUG", None):
        print("""JOBSTAMP: Dependencies up to date, """  # pragma: no cover
              """using cached value of {} from {}""".format(func.__name__,
                                                            stamp_file_name))

    with open(stamp_file_name) as stamp:
        return literal_eval(stamp.read().decode())
