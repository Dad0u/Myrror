import os

from file import File


PERCENT_HASH = 10


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


def search_files(path):
  """
  Creates a list of File objects for all the files in the dir (recursively)

  Lists all the files in the given dir
  Adds the attribute rel_path, the path of the file relative to the base folder
  """
  l = [File(n,path) for n in get_all_files(path)]
  print(f"found {len(l)} files in {path}")
  return l


def keep_matching(f,l,compare):
  """
  Only keep the files in l that match f based on the compare func
  """
  r = list(l)
  for fl in l:
    if not compare(f,fl):
      r.remove(fl)
  return r


def find_identical(src,l):
  r = []
  for f in l:
    if f.size == src.size:
      r.append(f)
  for f in list(r):
    if f.qhash != src.qhash:
      r.remove(f)
  for f in list(r):
    if f.partial_hash(PERCENT_HASH) != src.partial_hash(PERCENT_HASH):
      r.remove(f)
  return r


if __name__ == "__main__":
  import sys
  from multiprocessing import Pool
  src = os.path.abspath(sys.argv[1])+'/'
  dst = os.path.abspath(sys.argv[2])+'/'
  assert os.path.isdir(src),f"No such directory: {src}"
  assert os.path.isdir(dst),f"No such directory: {dst}"

  print("Searching for files...")
  #src_list = search_files(src)
  #dst_list = search_files(dst)
  with Pool(2) as p:
    src_list,dst_list = p.map(search_files,[src,dst])
  # path+nom+taille+datemodif OU taille+qhash
  # Keep the original list (will be used for local copies)
  full_dst_list = list(dst_list)
  # 1st pass: removing files with same Path, name, size and modified date
  dst_path_dict = {f.rel_path:f for f in dst_list}
  for f in list(src_list):
    if f.rel_path in dst_path_dict:
      f_dst = dst_path_dict[f.rel_path]
      if f.size == f_dst.size and f.mtime == f_dst.mtime:
        src_list.remove(f)
        dst_list.remove(f_dst)
  print(f"Ignoring {len(full_dst_list) - len(dst_list)} "
"files with same path, name, size and date")
  # Now, all the files in src_list must go to dst
  # 2 options: they already exist on dst or only on src
  for f in src_list:
    r = find_identical(f,full_dst_list)
    if r:
      print(f"{f.rel_path} exists on dst as {r[0].rel_path}")
