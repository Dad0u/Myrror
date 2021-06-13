from multiprocessing import Pool
from location import Location


class File(dict):
  """
  Class that represents a file

  Basically a dict with at least the keys
    name
    path
    size
  More keys can be added
  """
  def __init__(self, path, name, size):
    super().__init__()
    self['name'] = name
    self['path'] = path
    self['size'] = size


def build_file_list(loc: Location) -> list:
  """
  Takes a Location, returns the list of files in this location

  Each file is represented by a dict with 3 keys:
    - name: The name of the file
    - path: the RELATIVE path of the file
    - size: the size of the file in bytes
  """


def refine(groups: list, key: str) -> list:
  """
  Takes a list of groups of files

  Will divide the groups so that no group lives with the same key.
  key is a value that must be in all the elements of the groups
  """
  r = []
  for group in groups:
    if len(group) == 1:
      r.append(group)
      continue
    d = {}
    for element in group:
      val = element[key]
      if val in d:
        d[val].append(element)
      else:
        d[val] = [element]
    r.extend(d.values())
  return r


def compare(src: Location, dst: Location) -> dict:
  print("Enumerating files...", end='', flush=True)
  with Pool(2) as p:
    src_list, dst_list = p.map(build_file_list, (src, dst))
  print("Ok.")
  for f in src_list:
    f['location'] = 'src'
  for f in dst_list:
    f['location'] = 'dst'
  groups = refine([src_list + dst_list], 'size')
