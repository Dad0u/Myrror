import os
import hashlib
import pickle


def cachedfunc(savefile):
  """
  Decorator to save the results of a function

  Allows the result to be loaded instead of re-computed
  Only for funcs with hashable arguments !
  Result must be picklable
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


def lazyproperty(f):
  @property
  def wrapper(self,*args,**kwargs):
    if not hasattr(self,'_'+f.__name__):
      setattr(self,'_'+f.__name__,f(self,*args,**kwargs))
    return getattr(self,'_'+f.__name__)
  return wrapper


def md5(fname,bs=1048576):
  """
  Returns the MD5 checksum of the file at the given location
  """
  h = hashlib.md5()
  with open(fname,'rb') as f:
    chunk = f.read(bs)
    while chunk:
      h.update(chunk)
      chunk = f.read(bs)
    return h.digest()


def sha256(fname,bs=1048576):
  """
  Returns the SHA256 checksum of the file at the given location
  """
  h = hashlib.sha256()
  with open(fname,'rb') as f:
    chunk = f.read(bs)
    while chunk:
      h.update(chunk)
      chunk = f.read(bs)
    return h.digest()


def quick_hash_file(fname,bs=1024):
  """
  Returns a quicker hash of the file at the given location

  Collisions can happen easily, always perform a full hash in case of collision
  Warning! Changing the bs will change the value of the hash
  """
  size = os.path.getsize(fname)
  if size <= 4*bs:
    return md5(fname,bs)
  h = hashlib.md5()
  with open(fname,'rb') as f:
    h.update(f.read(bs))
    f.seek(size//2,0)
    h.update(f.read(bs))
    f.seek(-bs,2)
    h.update(f.read(bs))
  return h.digest()


def partial_hash(f,percent=10,bs=1048576):
  """
  Reads at least percent % of the file to make the hash
  """
  assert 0 < percent < 100
  size = os.path.getsize(f)
  if size <= 3*bs:
    return md5(f)
  h = hashlib.md5()
  nblocks = max(1,int(percent/100*size/bs/3))
  with open(f,'rb') as f:
    for i in range(nblocks):
      h.update(f.read(bs))
    f.seek(int((size*(.5-percent/600))),0)
    for i in range(nblocks):
      h.update(f.read(bs))
    f.seek(-bs*nblocks,2)
    for i in range(nblocks):
      h.update(f.read(bs))
  return h.digest()


@cachedfunc('md5.p')
def cached_md5(f,*args):
  return md5(f)


@cachedfunc('sha256.p')
def cached_sha256(f,*args):
  return md5(f)


@cachedfunc('quick_hashes.p')
def cached_quick_hash_file(f,*args):
  return quick_hash_file(f)


@cachedfunc('partial_hashes.p')
def cached_partial_hash(f,percent,*args):
  return partial_hash(f,percent)


def rm_prefix(s,prefix):
  """
  str.removeprefix is only implemented since Python 3.9...
  """
  if s.startswith(prefix):
    return s[len(prefix):]
  return s


class Local_file:
  def __init__(self,path,root):
    self.fullpath = os.path.abspath(path)
    assert os.path.exists(path),path
    self.rel_path = self.path_relative_to(os.path.abspath(root)+'/')
    self.root = root

  @lazyproperty
  def name(self):
    return os.path.basename(self.rel_path)

  @lazyproperty
  def size(self):
    return os.path.getsize(self.fullpath)

  @lazyproperty
  def mtime(self):
    return os.path.getmtime(self.fullpath)

  @lazyproperty
  def md5(self):
    return cached_md5(self.fullpath)

  @lazyproperty
  def sha256(self):
    return cached_sha256(self.fullpath)

  @lazyproperty
  def qhash(self):
     return cached_quick_hash_file(self.fullpath)

  def partial_hash(self,percent):
    return cached_partial_hash(self.fullpath,percent)

  def path_relative_to(self,root):
    #return rm_prefix(self.fullpath,os.path.abspath(root)+'/')
    return rm_prefix(self.fullpath,root)

  def __repr__(self):
    return f"File({self.rel_path})"

  def __getattr__(self,v):
    if v.startswith("parthash_"):
      percent = int(v[9:])
      assert 0 < percent < 100
      return self.partial_hash(percent)
    return object.__getattribute__(self,v)


class Remote_file:
  pass
