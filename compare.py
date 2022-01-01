from multiprocessing import Pool
# from itertools import repeat
from threading import Thread

from core import File, Location, listf, get


def refine(groups: list[list[File]], prop: str) -> list[list[File]]:
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


def apply_criteria(groups: list[list[File]], criteria) -> (
        list[list[File]], list[File]):
  """
  Takes a list of potential groups and refine them using the given criteria

  Returns a list of matching groups and a list of unique elements
  """
  uniques = []
  for crit in criteria:
    print(f"Computing {crit}...", end='', flush=True)
    # Make sure they all have the crit computed

    # Multiprocessing uses a copy of the File objects
    # -> Not saving the computed attributes in our instances !
    # with Pool(2) as p:
    #   p.starmap(get, zip(repeat(crit), split_src_dst(groups)))

    # Threaded version
    src, dst = split_src_dst(groups)
    src = [i for i in src if not hasattr(i, crit)]
    dst = [i for i in dst if not hasattr(i, crit)]
    tsrc = Thread(target=lambda: get(crit, src))
    tdst = Thread(target=lambda: get(crit, dst))
    tsrc.start()
    tdst.start()
    tsrc.join()
    tdst.join()

    # Serialized version
    # src, dst = split_src_dst(groups)
    # get(crit, src)
    # get(crit, dst)

    print("Ok.")

    print(f"Refining by {crit}...", end='', flush=True)
    groups = refine(groups, crit)
    groups, u = extract_unique(groups)
    uniques.extend(u)
    print("Ok.")
    print(f"{sum([len(i) for i in groups])} elements in {len(groups)} groups")
  return groups, uniques


def compare(src: Location,
            dst: Location,
            criteria: list[str]):
  """
  To compare two locations based on a list of criteria

  Takes two locations and a list of criteria to match the files
  Only supports a single list of criteria, they will all be tested in order
  The files in a group match on all the specified criteria
  """
  assert src != dst, "Trying to compare the same location!"
  print("Enumerating files...", end='', flush=True)
  with Pool(2) as p:
    src_list, dst_list = p.map(listf, (src, dst))
  print("Ok.")
  for f in src_list:
    f.src = True

  groups, uniques = apply_criteria([src_list + dst_list], criteria)
  return groups, uniques


def is_on_both_locations(group: list[File]) -> bool:
  """
  Check if the group contains Files on two different locations

  Returns True if two different locations are found
  False if there is only one
  Raises an error if there is more than two or the list is empty
  """
  s = set(f.loc for f in group)
  if len(s) not in [1, 2]:
    raise RuntimeError(f"is_on_both_locations got a group with {len(s)} "
                       " different locations !")
  return len(s) == 2


def multi_compare(src: Location, dst: Location,
                  criteria_lists: list[list[str]]):
  """
  To compare two locations based on a list of lists of criteria

  Takes two locations and a list of criteria to match the files
  Two files are considered matching if they match all the criteria of any list

  TODO: find a way to re-include the already matched files from source
  (see notes 01/01/2022)
  """
  assert src != dst, "Trying to compare the same location!"
  print("Enumerating files...", end='', flush=True)
  with Pool(2) as p:
    src_list, dst_list = p.map(listf, (src, dst))
  print("Ok.")
  for f in src_list:
    f.src = True

  unmatched = [src_list + dst_list]
  matched = []
  for criteria in criteria_lists:
    print("Working on the list of criteria:", criteria)
    groups, unmatched = apply_criteria(unmatched, criteria)
    for g in groups:
      if is_on_both_locations(g):
        matched.append(g)
      else:
        unmatched.extend(g)
    if not unmatched:
      return matched, unmatched

    unmatched = [unmatched]
  return matched, unmatched[0]

