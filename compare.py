from multiprocessing import Pool

from core import File, Location, listf, get


def refine(groups: list[list[File]], prop: str) -> list:
  """
  Takes a list of groups of files

  Will divide the groups so that all the elements in a group have the same
  value of prop
  prop is a value that must exist as an attribute in all the elements of the
  groups

  Ex:
  >>>a.cap = b.cap = c.cap = False
  >>>A.cap = B.cap = True
  >>>l = [[a, b, A], [c, B]]
  >>>refine(l, 'cap')
  [[a, b], [A], [c], [B]]
  (order is not guaranteed)
  """
  r = []
  for group in groups:
    if len(group) == 1:
      r.append(group)
      continue
    d = {}
    for element in group:
      val = getattr(element, prop)
      if val in d:
        d[val].append(element)
      else:
        d[val] = [element]
    r.extend(d.values())
  return r


def compare(src: Location, dst: Location, criteria: list[str]) -> dict:
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
  assert src != dst, "Trying to compare the same location!"
  print("Enumerating files...", end='', flush=True)
  with Pool(2) as p:
    src_list, dst_list = p.map(listf, (src, dst))
  print("Ok.")
  for f in src_list:
    f['location'] = 'src'
  for f in dst_list:
    f['location'] = 'dst'
  groups = refine([src_list + dst_list], 'size')
