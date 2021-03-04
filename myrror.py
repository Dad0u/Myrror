from multiprocessing import Pool
import os
from file import Local_file, Remote_file


def get_all_files(d):
  """
  Get all the files in the folder (recursively)
  """
  r = []
  absd = os.path.abspath(d)
  l = os.listdir(absd)
  for f in l:
    full = os.path.join(absd,f)
    if os.path.isdir(full):
      r += get_all_files(full)
    else:
      r.append(full)
  return r


class Location:
  """
  Class meant to represent a local or remote folder
  """
  def __init__(self,s):
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
    self.flist = [Local_file(f,self.root) for f in get_all_files(self.root)]


def mkloc(p):
  loc = Location(p)
  loc.discover_files()
  print(f"Found {len(loc.flist)} files on {loc}")
  return loc


# size is implied
default_check = [['rel_path','mtime'],['qhash','parthash_10']]
strict_check = [['qhash','sha256']]


def group(l,attr):
  """
  Refine a grouping using the given attribute

  Takes and returns a list of tuples of lists of files
  [([src1,src2],[dst1]),([src3],[]),([],[dst3])]
  in the tuple, both lists can hold any number of files
  except 0 on both sides
  """
  r = []
  for ls,ld in l:
    ds,dd = {},{}
    for f in ls:
      k = getattr(f,attr)
      if k in ds:
        ds[k].append(f)
      else:
        ds[k] = [f]
    for f in ld:
      k = getattr(f,attr)
      if k in dd:
        dd[k].append(f)
      else:
        dd[k] = [f]
    for k,v in ds.items():
      r.append((v,dd.pop(k,[])))
    for v in dd.values():
      r.append(([],v))
  return r


def extract_unique(l):
  """
  Extract the files that are uniques and on only one side

  Takes the same input as group and returns two of them
  """
  unique,non_unique = [],[]
  for ls,ld in l:
    if len(ls)+len(ld) == 1:
      unique.append((ls,ld))
    else:
      non_unique.append((ls,ld))
  return unique,non_unique


def split(unique_l):
  """
  Takes the list of groups of unique files and flattens it into two lists

  [([fa],[]),([],[fb])] -> [fa],[fb]
  """
  s,d = [],[]
  for a,b in unique_l:
    if a:
      s.append(a[0])
    else:
      d.append(b[0])
  return s,d


def compare_folders(src,dst,check=default_check):
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
  l = group([(src.flist,dst.flist)],'size')
  matched = []
  # If all the checks in a check group are verified, the files are considered
  # identical
  l = group([(src.flist,dst.flist)],'size')
  for check_group in check:
    print(f"Starting group {check_group}")
    print(f"matched: {matched}")
    unique,non_unique = extract_unique(l)
    print(f"unique: {unique}")
    print(f"non unique: {non_unique}")
    for attr in check_group:
      print(f"  Checking {attr}")
      l = group(non_unique,attr)
      new_u,non_unique = extract_unique(l)
      print(f"new unique: {new_u}")
      print(f"Non unique: {non_unique}")
      unique.extend(new_u)
    matched.extend(non_unique)
    l = group([split(unique)],'size')
  #return matched,*split(unique)
  return matched+unique


def sync_folders(src,dst,check=default_check):
  #src = mkloc(src)
  #dst = mkloc(dst)
  with Pool(2) as p:
    src,dst = p.map(mkloc,[src,dst])
  matches = compare_folders(src,dst)
  src_only = []
  dst_only = []
  m = []
  # This next loop will split the groups in 3:
  # Files only on src, only on dst and on both sides
  for a,b in matches:
    if not b:
      src_only.append(a)
    elif not a:
      dst_only.extend(b)
    else:
      m.append((a,b))
  return m,src_only,dst_only
  # Now m only contains matches that are on both sides !
  return m,src_only,dst_only


if __name__ == '__main__':
  import sys
  src,dst = sys.argv[1:]
  m,us,ud = sync_folders(src,dst)
