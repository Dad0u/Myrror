from multiprocessing import Pool
from file import File


class Location:
  """
  Class meant to represent a local or remote folder
  """
  def __init__(self,s):
    pass
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


def same(attr):
  def f(a,b):
    return getattr(a,attr) == getattr(b,attr)
  return f


def sync_folders(src,dst):
  #src,dst = Location(src),Location(dst)
  #src.discover_files()
  #dst.discover_files()
  def mkloc(p):
    loc = Location(p)
    loc.discover_files()
    print(f"Found {len(loc.flist)} files on {loc}")
    return loc
  with Pool(2) as p:
    src,dst = p.map(mkloc,[src,dst])
  # Those files are considered identical
  m = get_match(src.flist,dst.flist,[same(i) for i in ['name','size','mtime']])
  # Maybe group ALL the files for local matches...
  # Then, compute a qhash for all the remaining files of a size that exists on both sides
  # And finally, a real hash (and store it)





if __name__ == '__main__':
  import sys
  src,dst = sys.argv[1:]
  sync_folders(src,dst)
