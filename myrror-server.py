import os


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
    root = sys.argv[2]
    for fullpath in get_all_files(root):
      print(f"#n>{os.path.relpath(fullpath,root)}")
      print(f"#s>{os.path.getsize(fullpath)}")
      print(f"#t>{os.path.getmtime(fullpath)}")
  else:
    raise NameError("Unknown command: "+sys.argv[1])
