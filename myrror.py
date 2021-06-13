from multiprocessing import Pool
import os
from file import Local_file


def get_all_files(d):
  """
  Get all the files in the folder (recursively)
  """
  r = []
  absd = os.path.abspath(d)
  l = os.listdir(absd)
  for f in l:
    full = os.path.join(absd, f)
    if os.path.isdir(full):
      r += get_all_files(full)
    else:
      r.append(full)
  return r


class Location:
  """
  Class meant to represent a local or remote folder
  """
  def __init__(self, s):
    # TODO parse the string, detect if remote or local
    self.remote = False
    self.root = s

  def discover_files(self):
    """
    Updates the list of files at this location (recursively)
    """
    if self.remote:
      self.discover_files_remote()
    else:
      self.discover_files_local()

  def discover_files_local(self):
    self.flist = [Local_file(f, self.root) for f in get_all_files(self.root)]


def mkloc(p):
  loc = Location(p)
  loc.discover_files()
  print(f"Found {len(loc.flist)} files on {loc}")
  return loc


# size is implied
default_check = [['rel_path', 'mtime'], ['qhash', 'parthash_10']]
strict_check = [['qhash', 'sha256']]


def group(l, attr):
  """
  Refines a grouping using the given attribute

  Takes and returns a list of tuples of lists of files
  [([src1,src2],[dst1]),([src3],[]),([],[dst3])]
  in the tuple, both lists can hold any number of files
  except 0 on both sides
  """
  r = []
  for ls, ld in l:
    ds, dd = {}, {}
    for f in ls:
      k = getattr(f, attr)
      if k in ds:
        ds[k].append(f)
      else:
        ds[k] = [f]
    for f in ld:
      k = getattr(f, attr)
      if k in dd:
        dd[k].append(f)
      else:
        dd[k] = [f]
    for k, v in ds.items():
      r.append((v, dd.pop(k, [])))
    for v in dd.values():
      r.append(([], v))
  return r


def extract_unique(l):
  """
  Extract the files that are uniques and on only one side

  Takes the same input as group and returns two of them
  """
  unique, non_unique = [], []
  for ls, ld in l:
    if len(ls) + len(ld) == 1:
      unique.append((ls, ld))
    else:
      non_unique.append((ls, ld))
  return unique, non_unique


def split(unique_l):
  """
  Takes the list of groups of unique files and flattens it into two lists

  [([fa],[]),([],[fb])] -> [fa],[fb]
  """
  s, d = [], []
  for a, b in unique_l:
    if a:
      s.append(a[0])
    else:
      d.append(b[0])
  return s, d


def compare_folders(src, dst, check=default_check):
  """
  Takes two locations, compares them and returns the matches

  Returns a list of tuples of 2 lists
  Each tuple contains matched files
  The first list of the tuple contains the files on src only and the second
  the ones on dst only
  """
  # For each sequence in a check, keep groups of files
  # that fullfill all the checks
  # Store the partial and full hashes
  # (and qhashes ? -> benchmark to see if useful or not)
  l = group([(src.flist, dst.flist)], 'size')
  matched = []
  # If all the checks in a check group are verified, the files are considered
  # identical
  l = group([(src.flist, dst.flist)], 'size')
  for check_group in check:
    print(f"Starting group {check_group}")
    print(f"matched: {matched}")
    unique, non_unique = extract_unique(l)
    print(f"unique: {unique}")
    print(f"non unique: {non_unique}")
    for attr in check_group:
      print(f"  Checking {attr}")
      l = group(non_unique, attr)
      new_u, non_unique = extract_unique(l)
      print(f"new unique: {new_u}")
      print(f"Non unique: {non_unique}")
      unique.extend(new_u)
    matched.extend(non_unique)
    l = group([split(unique)], 'size')
  return matched + unique


def get_actions(matches):
  print("get_actions is processing", matches)
  src_only = []
  dst_only = []
  m = []
  # This loop will split the groups in 3:
  # Files only on src, only on dst and on both sides
  # Note that src_only is a list of lists and dst_only simply a list
  for a, b in matches:
    if not b:
      src_only.append(a)
    elif not a:
      dst_only.extend(b)
    else:
      m.append((a, b))
  print("m=", m)
  # Now m only contains matches that are on both sides !
  # return m,src_only,dst_only
  # Now let's get to the actions:
  # eausy part: delete what is only on dst,
  # remote copy one file of each group only on src
  # Then, thigns get complicated...
  action = {}
  action['rm'] = [f.rel_path for f in dst_only]
  action['local_cp_pre'] = []
  action['mv'] = []
  action['remote_cp'] = []
  action['local_cp_post'] = []

  # Removing the groups that are strictly identical
  new_m = []
  for s, d in m:
    if len(s) != len(d):
      new_m.append((s, d))
      continue
    if set([f.rel_path for f in s]) != set([f.rel_path for f in d]):
      new_m.append((s, d))
  m = new_m
  print("After removing identical groups, m=", m)

  # Now, removing matching pairs as long as they leave at least one in dst
  # Why ? Beacause if we have ([a,b],[a]), doing ([b],[]) would trigger a
  # unnecessary remote copy when we can do a local copy a->b
  for s, d in m:
    for i in list(s):
      if i.rel_path in [f.rel_path for f in d] and len(d) > 1:
        s.remove(i)
        d.remove([f for f in d if f.rel_path == i.rel_path][0])
  # Now, the list is as minimal as possible
  # Let's get to creating the actions.
  print("After removing unused pairs, m=", m)

  # ###################################### OLD CODE #######################
  for s, d in m:
    for i, j in zip(s, d):
      action['mv'].append((j.rel_path, i.rel_path))
      # action['mv'].append((j.rel_path,temp_name(i.rel_path)))
      # if temp_name(i.rel_path) != i.rel_path:
      #  action['final_mv'].append((temp_name(i.rel_path),i.rel_path))
    diff = len(s) - len(d)
    if diff > 0:
      for i in s[diff:]:
        action['local_cp_pre'].append((d[0].rel_path, i.rel_path))
    elif diff < 0:
      for i in d[diff:]:
        action['rm'].append(i.rel_path)
  for l in src_only:
    action["remote_cp"].append(l[0].rel_path)
    for f in l[1:]:
      action["local_cp_post"].append((l[0].rel_path, f.rel_path))
  ##########################################################################
  return action


def sync_folders(src, dst, check=default_check):
  with Pool(2) as p:
    src, dst = p.map(mkloc, [src, dst])
  matches = compare_folders(src, dst)
  action = get_actions(matches)
  return action


if __name__ == '__main__':
  import sys
  src, dst = sys.argv[1:]
  a = sync_folders(src, dst)
