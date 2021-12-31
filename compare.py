from multiprocessing import Pool
# from itertools import repeat
from threading import Thread

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


def extract_unique(groups: list[list]):
  """
  Takes a list of lists

  All the empty lists are removed, the list containing one element are removed
  and returned separately
  Returns a tuple of two elements: the clean list and the single elements
  Example:
  [[1, 2], [3], [4], [5, 6, 7], [], [8]]
  -> ([[1, 2], [5, 6, 7]], [3, 4, 8])
  """
  r, u = [], []
  for g in groups:
    if len(g) == 1:
      u.extend(g)
    elif len(g) > 1:
      r.append(g)
  return r, u


def split_src_dst(groups: list[list]):
  """
  Takes a list of lists of Files, flattens and splits the Files in two groups:
  the ones with the src attribute and the ones without
  """
  src, dst = [], []
  for g in groups:
    for f in g:
      if hasattr(f, 'src'):
        src.append(f)
      else:
        dst.append(f)
  return src, dst


def compare(src: Location,
            dst: Location,
            criteria: list[str]):
  """
  To compare two locations based on a list of criteria

  Takes two locations and a list of criteria to match the files
  Returns a list of list of Files. Each list is a matching group
  """
  assert src != dst, "Trying to compare the same location!"
  print("Enumerating files...", end='', flush=True)
  with Pool(2) as p:
    src_list, dst_list = p.map(listf, (src, dst))
  print("Ok.")
  for f in src_list:
    f.src = True

  print("Refining by size...", end='', flush=True)
  groups = refine([src_list + dst_list], 'size')
  groups, uniques = extract_unique(groups)
  print("Ok.")
  print(f"{sum([len(i) for i in groups])} elements in {len(groups)} groups")
  for crit in criteria:
    print(f"Computing {crit}...", end='', flush=True)
    # Make sure they all have the crit computed

    # Multiprocessing uses a copy of the File objects
    # -> Not saving the computed attributes in our instances !
    # with Pool(2) as p:
    #   p.starmap(get, zip(repeat(crit), split_src_dst(groups)))

    # Threaded version
    # src, dst = split_src_dst(groups)
    # src = [i for i in src if not hasattr(i, crit)]
    # dst = [i for i in dst if not hasattr(i, crit)]
    # tsrc = Thread(target=lambda: get(crit, src))
    # tdst = Thread(target=lambda: get(crit, dst))
    # tsrc.start()
    # tdst.start()
    # tsrc.join()
    # tdst.join()

    # Serialized version
    src, dst = split_src_dst(groups)
    get(crit, src)
    get(crit, dst)

    print("Ok.")

    print(f"Refining by {crit}...", end='', flush=True)
    groups = refine(groups, crit)
    groups, u = extract_unique(groups)
    uniques.extend(u)
    print("Ok.")
    print(f"{sum([len(i) for i in groups])} elements in {len(groups)} groups")
  return groups, uniques
