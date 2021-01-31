import os
import sys
import pickle
import hashlib
import shutil


TRASHDIR = "trash/"


def cachedfunc(savefile):
  """
  Decorator to save the results of a function

  Allows the result to be loaded instead of re-computed
  Only for funcs with hashable arguments !
  Result mut be picklable
  """
  def deco(f):
    def newf(*args):
      args = tuple(args)
      try:
        with open(savefile,'rb') as sf:
          saved = pickle.load(sf)
      except FileNotFoundError:
        saved = {}
      if args not in saved:
        saved[args] = f(*args)
        with open(savefile,'wb') as sf:
          pickle.dump(saved,sf)
      return saved[args]
    return newf
  return deco


def hash_file(fname,bs=1048576):
  """
  Returns the hash of the file at the given location
  """
  h = hashlib.md5()
  with open(fname,'rb') as f:
    chunk = f.read(bs)
    while chunk:
      h.update(chunk)
      chunk = f.read(bs)
    return h.digest()


def quick_hash_file(fname,bs=1048576):
  """
  Returns a quicker hash of the file at the given location

  Collisions can happen easily, always perform a full hash in case of collision
  Warning! Changing the bs will change the value of the hash
  """
  size = os.path.getsize(fname)
  if size < 3*bs:
    return hash_file(fname,bs)
  h = hashlib.md5()
  with open(fname,'rb') as f:
    h.update(f.read(bs))
    f.seek(size//2,0)
    h.update(f.read(bs))
    f.seek(-bs,2)
    h.update(f.read(bs))
  return h.digest()


@cachedfunc('hashes.p')
def get_qhash(*args):
  """
  To retrieve from the cache only if size and date match
  """
  return quick_hash_file(args[0])


def props(f):
  s = os.path.getsize(f)
  t = os.path.getmtime(f)
  h = get_qhash(f,s,t)
  return (f,s,t,h)


def rm_prefix(s,prefix):
  """
  str.removeprefix is only implemented since 3.9...
  """
  if s.startswith(prefix):
    return s[len(prefix):]
  return s


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
      r.append(props(full))
  return r


def build_dict(l):
  """
  Creates a dict where the keys are the prop (size, date and qhash)
  and each value is a list of the corresponding files
  """
  d = {}
  for f,s,t,h in l:
    key = (s,t,h)
    if key not in d:
      d[key] = [f]
    else:
      d[key].append(f)
  return d


def get_src_only(src,dst,flatten=False):
  """
  Returns the files that are only on one side

  If flatten=True, it is only a list of names
  else, it is a list of lists, each one consisting of identical files
  ex: [[f1,f2],[f3]] means that f1 and f2 are identical
  This func also removes the corresponding files from the dict
  """
  r = []
  for k in dict(src):
    if k not in dst:
      if flatten:
        r.extend(src[k])
      else:
        r.append(src[k])
      del src[k]
  return r


def get_identical(src_dict, dst_dict):
  """
  List of tuples with 2 lists:

  The identical files on src and dst
  """
  r = []
  for t,files in dst_dict.items():
    r.append((files,src_dict[t]))
  return r


def get_actions(src_dict,dst_dict):
  """
  Recap all the actions to be performed to sync the trees

  Empty dirs are not created or removed
  """
  # Executed in the following order
  final_actions = {i:[] for i in ['remote_cp','local_cp','mv','rm']}
  # remote_cp: (src_file, dst_file)
  # local_cp: (dst_file, dst_file)
  # mv: (dst_file, dst_file
  # rm: dst_file
  # Removing file groups that were not altered
  for k,l in dict(src_dict).items():
    if dst_dict.get(k) == l:
      del src_dict[k]
      del dst_dict[k]
      continue
    for f in l:
      if f in dst_dict.get(k,[]):
        src_dict[k].remove(f)
        dst_dict[k].remove(f)
  # Only src
  to_cp = get_src_only(src_dict,dst_dict)
  for l in to_cp:
    final_actions['remote_cp'].append((l[0],l[0])) # Only remote copy one
    print(f"{l[0]} is only on src, remote copy necessary")
    for i in l[1:]:
      print(f"{i} is only on src, but we can use {l[0]} to local copy")
      final_actions['local_cp'].append((l[0],i)) # And local copy the others
  # Only dst
  final_actions['rm'].extend(get_src_only(dst_dict,src_dict,flatten=True))
  print(f"{final_actions['rm']} are only on dst, to be removed")
  # Both but need to be moved/copied/deleted
  local_actions = get_identical(src_dict, dst_dict)
  for old,new in local_actions:
    for i,j in zip(old,new):
      print(f"Locally moving {i} to {j}")
      final_actions['mv'].append((i,j)) # Easy part, the moves
    if len(new) > len(old): # More on src, local copies required
      for i in new[len(old):]:
        print(f"{old[0]} can be used to local copy {i}")
        final_actions['local_cp'].append((old[0],i))
    elif len(new) < len(old): # More on dst, removes required
      for i in old[len(new):]:
        final_actions['rm'].append(i)
        print(f"{i} is removed as it was a duplicate")
  return final_actions


def cp(f1,f2):
  os.makedirs(os.path.dirname(f2),exist_ok=True)
  shutil.copy2(f1,f2)


def mv(f1,f2):
  os.makedirs(os.path.dirname(f2),exist_ok=True)
  shutil.move(f1,f2)


def rm(f1):
  os.remove(f1)


if __name__ == "__main__":
  src = os.path.abspath(sys.argv[1])+'/'
  dst = os.path.abspath(sys.argv[2])+'/'
  assert os.path.isdir(src),f"No such directory: {src}"
  assert os.path.isdir(dst),f"No such directory: {dst}"

  src_list = get_all_files(src)
  dst_list = get_all_files(dst)
  src_list = [(rm_prefix(f,src),*p) for f,*p in src_list]
  dst_list = [(rm_prefix(f,dst),*p) for f,*p in dst_list]
  src_dict,dst_dict = build_dict(src_list),build_dict(dst_list)

  actions = get_actions(src_dict,dst_dict)
  for k in ['remote_cp','local_cp','mv','rm']:
    print(f"\n=========  {k.upper()}  =========\n")
    for v in actions[k]:
      if isinstance(v,tuple):
        print(v[0],' -> ', v[1])
      else:
        print(v)
  print("\n")
  if input("Continue?").lower() != 'y':
    raise KeyboardInterrupt
  os.makedirs(TRASHDIR,exist_ok=True)
  for s,d in actions['remote_cp']:
    print(f"Remote copy from {s} to {d}")
    cp(os.path.join(src,s),os.path.join(dst,d))
  for s,d in actions['local_cp']:
    print(f"Local copy from {s} to {d}")
    cp(os.path.join(dst,s),os.path.join(dst,d))
  for s,d in actions['mv']:
    print(f"Move from {s} to {d}")
    mv(os.path.join(dst,s),os.path.join(dst,d))
  for s in actions['rm']:
    print(f"Remove {s}")
    #rm(os.path.join(dst,s))
    os.makedirs(os.path.join(TRASHDIR,os.path.dirname(s)),exist_ok=True)
    mv(os.path.join(dst,s),os.path.join(TRASHDIR,os.path.dirname(s)))
