
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


def group_simple(l, criteria):
  """
  Pretty straightforward: only match if all the keys match
  """
  uniques, nonuniques = remove_uniques(l)
  for criterion in criteria:
    print(f"{uniques=}")
    print(f"{nonuniques=}")
    l = refine(nonuniques, criterion)
    new_uniques, nonuniques = remove_uniques(l)
    uniques.extend(new_uniques)
  print(f"{uniques=}")
  print(f"{nonuniques=}")
  return uniques + nonuniques


def group_multi(l, criteria):
  """
  Much more complex:
  Match if all the keys of one list match
  BUT do not check when a match is already known

  Strategy: Group based on the 1st list.
  Remove all but one from each group and start over for the second
  New groups are the joined to the previous
  """
  if isinstance(criteria[0], str):
    criteria = [criteria]
  groups = []
  nonuniques = [l]
  for critgroup in criteria:
    uniques = []
    nonuniques = [l]
    for criterion in critgroup:
      l = refine(nonuniques, criterion)
      new_uniques, nonuniques = remove_uniques(l)
      uniques.extend(new_uniques)
    print(f"{uniques=}")
    print(f"{nonuniques=}")
    l = uniques + nonuniques


def fuse_groups(l1, l2):
  """
  Groups the matches in l1 and l2

  Simply put, fusing [[a, b], [c], [d]] and [[a], [b, c], [d]]
  gives [[a, b, c], [d]]
  """
  dftog1 = {}
  dgtof1 = {}
  for i, gp in enumerate(l1):
    for f in gp:
      dftog1[f.pname] = i
    dgtof1[i] = [f.pname for f in gp]
  dftog2 = {}
  dgtof2 = {}
  for i, gp in enumerate(l2):
    for f in gp:
      dftog2[f.pname] = i
    dgtof2[i] = [f.pname for f in gp]
  for gid1, flist1 in dgtof1.items():
    glist2 = [dftog2[f] for f in flist1 if f in dftog2]
    newf = sum([dgtof2[g] for g in glist2], [])





if __name__ == '__main__':

  a = [[1, 2], [3], [4], [5]]
  b = [[2, 3], [4, 6]]
  print(f"{a=}", f"{b=}")
  print(fuse_groups(a, b))

  """
  f1 = {'name': 'a',
      'size': 2,
      'chk': 234234}

  f2 = {'name': 'b',
      'size': 2,
      'chk': 234234}

  f3 = {'name': 'a',
      'size': 1,
      'chk': 234234}

  f4 = {'name': 'a',
      'size': 2,
      'chk': 234234}

  print(group_simple([[f1, f2, f3, f4]], ['name', 'size']))
  """
