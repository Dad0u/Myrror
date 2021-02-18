from multiprocessing import Pool
from file import File


class Location:
  """
  Class meant to represent a local or remote folder
  """
  def __init__(self,s):
    # TODO parse the string, detect if remote or local
    self.remote = False

  def discover_files(self):
    """
    Updates the list of files at this location (recursively)
    """
    if self.remote:
      self.discover_files_remote()
    else:
      self.discover_files_local()


def get_match(src,dst,comparison):
  """
  Returns the files on src and dst that may be identical
  """
  if isinstance(comparison,list):
    comparison = lambda a,b: all(c(a,b) for c in comparison)
  # QUESTION: how to return the matches ?
  # List of tuples ?
  # What about "inner" matches (files with several instances on a side)
  # A: A list of tuples of lists (oof)
  # [([src1,src2,...],[dst1,...]),([],[]),...]



def same(attr):
  def f(a,b):
    return getattr(a,attr) == getattr(b,attr)
  return f


def mkloc(p):
  loc = Location(p)
  loc.discover_files()
  print(f"Found {len(loc.flist)} files on {loc}")
  return loc

# size is implied
default_check = [['name','path','size','mtime'],['qhash','parthash_10']]
strict_check = [['qhash','sha256']]

def sync_folders(src,dst):
  #src,dst = Location(src),Location(dst)
  #src.discover_files()
  #dst.discover_files()
  with Pool(2) as p:
    src,dst = p.map(mkloc,[src,dst])
  # Those files are considered identical
  # For each sequence in a check, keep groups of files that fullfill all the checks
  # Maybe group ALL the files for local matches...
  # Store the partial and full hashes (and qhashes ? -> benchmark to see if useful or not)





if __name__ == '__main__':
  import sys
  src,dst = sys.argv[1:]
  sync_folders(src,dst)
