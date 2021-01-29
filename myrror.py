import os
import sys
import pickle
import hashlib


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


def get_src_only(src,dst):
  r = []
  for k in dict(src):
    if k not in dst:
      r.extend(src[k])
      del src[k]
  return r


def get_mv(src_dict, dst_dict):
  r = []
  for t,files in dst_dict.items():
    r.append((files,src_dict[t]))
  return r


if __name__ == "__main__":
  src = os.path.abspath(sys.argv[1])+'/'
  dst = os.path.abspath(sys.argv[2])+'/'
  assert os.path.exists(src),f"Could not find source: {src}"
  assert os.path.exists(dst),f"Could not find source: {dst}"
  src_list = get_all_files(src)
  dst_list = get_all_files(dst)
  src_list = [(rm_prefix(f,src),*p) for f,*p in src_list]
  dst_list = [(rm_prefix(f,dst),*p) for f,*p in dst_list]
  #src_dict = {p:rm_prefix(f,src) for f,*p in src_list}
  #dst_dict = {p:rm_prefix(f,dst) for f,*p in dst_list}
  for elt in list(src_list):
    #print(elt[0])
    if elt in dst_list:
      src_list.remove(elt)
      dst_list.remove(elt)
  src_dict,dst_dict = build_dict(src_list),build_dict(dst_list)
  to_cp = get_src_only(src_dict,dst_dict)
  to_rm = get_src_only(dst_dict,src_dict)
  to_mv = get_mv(src_dict, dst_dict)
