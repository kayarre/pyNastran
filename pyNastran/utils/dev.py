"""
defines:
 - fnames = get_files_of_type(dirname, extension='.txt',
                              max_size=100., limit_file='no_dig.txt')
 - msg = list_print(lst, float_fmt='%-4.2f')

"""
import os
from typing import Any

import numpy as np
from pyNastran.utils import PathLike


def get_files_of_type(dirname: str, extension: str='.txt',
                      max_size_mb: float=100., limit_file: str='no_dig.txt',
                      skip_folder_file: str='skip_folder.txt') -> list[str]:
    """
    Gets the list of all the files with a given extension in the specified directory

    Parameters
    ----------
    dirname : str
        the directory name
    extension : str; default='.txt'
        list of filetypes to get
    max_size_mb : float; default=100.0
        >0.0: size in MB for max file size
        <=0.0: no limit
    limit_file : str; default=no_dig.txt
        the presence of this file indicates no folder digging
        should be done on this folder
    skip_file : str; skip_folder.txt
        the presence of this file indicates the folder should be skipped
        should be done on this folder

    Returns
    -------
    files : list[str]
        list of all the files with a given extension in the specified directory

    """
    filenames2: list[str] = []
    if not os.path.exists(dirname):
        return filenames2

    if not isinstance(dirname, PathLike):
        raise TypeError('dirname must be a PathLike object')
    if not isinstance(extension, str):
        raise TypeError(f'extension={extension!r} must be a str')

    filenames = os.listdir(dirname)
    if skip_folder_file in filenames:
        print(f'found skip_file in dirname={dirname}')
        return filenames2

    allow_digging = True
    if limit_file in filenames:
        allow_digging = False

    for filenamei in filenames:
        filename = os.path.join(dirname, filenamei)
        if os.path.isdir(filename):
            if allow_digging:
                filenames2 += get_files_of_type(filename, extension, max_size_mb)
                #assert len(filenames2) > 0, dirnamei
            else:
                print('no digging in filename=%s; dirname=%s' % (filename, dirname))
        elif (os.path.isfile(filename) and
              os.path.splitext(filenamei)[1].endswith(extension) and
              max_size_mb <= 0.0):
            filenames2.append(filename)
        elif (os.path.isfile(filename) and
              os.path.splitext(filenamei)[1].endswith(extension) and
              os.path.getsize(filename) / 1048576. <= max_size_mb):
            filenames2.append(filename)
    return filenames2


def get_files_of_types(dirname: str, extensions: list[str],
                       max_size_mb: float=0.) -> list[str]:
    """
    Gets a recursive list of files with specific file extensions

    Parameters
    ----------
    dirname : str
        the directory name
    extensions : list[str]
        list of filetypes to get
    max_size_mb : float; default=100.0
        >0.0: size in MB for max file size
        <=0.0: no limit

    Returns
    -------
    files : list[str]
        list of all the files with a given extension in the specified directory

    """
    assert isinstance(extensions, list), f'extensions={extensions} must be a list'
    fnames = []
    for extension in extensions:
        fnamesi = get_files_of_type(dirname, extension, max_size_mb)
        fnames.extend(fnamesi)
    return fnames


def list_print(lst: list[Any], float_fmt: str='%-4.2f') -> str:
    """
    Prints a list or numpy array in an abbreviated format.
    Supported element types: None, string, numbers. Useful for debugging.

    Parameters
    ----------
    lst : list / numpy array
        the value to print

    Returns
    -------
    msg : str
        the clean string representation of the object

    """
    def _print(val):
        if val is None or isinstance(val, str):
            return str(val)
        if isinstance(val, float):
            return float_fmt % val
        try:
            return '%g' % val
        except TypeError:
            print("parameter = %r" % val)
            raise

    if len(lst) == 0:
        return '[]'

    try:
        # TODO: remove try block and fix bug in OP2 code or add a warning message
        if isinstance(lst, np.ndarray) and lst.ndim == 2:
            row, col = lst.shape
            return (
                "["+",\n ".join(["["+",".join(
                    [float_fmt % lst[i, j]
                     for j in range(col)]) + "]" for i in range(row)])+"]")
        return "[" + ", ".join([_print(a) for a in lst]) + "]"
    except Exception: # not a list
        return _print(lst)
