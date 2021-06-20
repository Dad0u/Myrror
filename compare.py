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


def remove_uniques(groups: list) -> list:
  return [i for i in groups if len(i) == 1], [i for i in groups if len(i) != 1]


def compare(src: Location, dst: Location, criteria: list) -> dict:
  """
  To compare two locations based on a list of criteria

  Takes two locations and a list of criteria to match the files
  Returns a list of list of Files. Each list is a matching group
  Each file has a 'location' key either set to 'src' or 'dst'
  The list of criteria can be a list of keys or a list of lists of keys
  In the first case, all the keys must match, in the second, all the keys of
  at least one list must match. It can be used to accelerate comparison in the
  where a set of attribute is less likely to match easier to compute and still
  reliable (example: in some cases, name, path and mtime matching is enough to
  exclude a content comparison)
  """
  if isinstance(criteria[0], str):
    criteria = [criteria]
  print("Enumerating files...", end='', flush=True)
  with Pool(2) as p:
    src_list, dst_list = p.map(build_file_list, (src, dst))
  print("Ok.")
  for f in src_list:
    f['location'] = 'src'
  for f in dst_list:
    f['location'] = 'dst'
  groups = refine([src_list + dst_list], 'size')
  unique, nonunique = remove_uniques(groups)

  for cgp in criteria:
    for criterion in cgp:

