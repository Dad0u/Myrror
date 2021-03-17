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
    full = os.path.join(absd,f)
    if os.path.isdir(full):
      r += get_all_files(full)
    else:
      r.append(full)
  return r


if __name__ == '__main__':
  import sys
  assert len(sys.argv) == 3,"Invalid command"
  if sys.argv[1] == "list":
    for name in get_all_files(sys.argv[2]):
      print(name)
      f = Local_file(name,'.')
      print(f.size)
      print(f.mtime)
  if sys.argv[1].startswith("get_"):
    attr = sys.argv[1][4:]
    flist = sys.argv[2]
    r = []
    for f in flist:
      r.append(getattr(Local_file(f,'/'),attr))
    print(r) # TODO
