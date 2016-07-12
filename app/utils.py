import string
from typing import List


def chunks(l: List, n: int) -> List[List]:
    """Split list into n-sized chunks

    Splits the list, l, into chunks of size n. The last chunk may be smaller
    than n.

    Args:
        l: the list to be split
        n: the size of returned chunks
    Returns:
        a list of chunks
    """
    cs = []
    for i in range(0, len(l), n):
        cs.append(l[i:i+n])
    return cs


def sanitize_filename(filename: str, ext: str = None) -> str:
    """ Sanitize filenames

    Creates a sanatized filename by removing any non-alphanumeric characters
    except '.' and '-' and replacing all spaces with underscores.

    Args:
        filename: the input name to be sanatized sans extention
        ext: the file extension(eg. 'zip'). This is not sanitized.
    Returns:
        The sanitized filename with the specified extension
    """
    allowed_chars = set(string.digits+string.ascii_letters+".- ")
    sane_fname = [c for c in filename if c in allowed_chars]
    sane_fname = "".join(sane_fname).strip()
    sane_fname = sane_fname.replace(' ', '_')
    if ext is not None:
        return "{}.{}".format(sane_fname, ext)
    else:
        return sane_fname
