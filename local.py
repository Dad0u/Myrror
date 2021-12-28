from file import File
import os
import hashlib
import pickle
from time import time

SAVE_DELAY = 60  # When reading properties, save them every X seconds


def get_all_files(d):
  """
  Get all the files in the folder (recursively)
  """
  r = []
  absd = os.path.abspath(d)
  l = os.listdir(absd)
  for f in l:
    if f.startswith('.'):
      continue
    full = os.path.join(absd, f)
    if os.path.isdir(full):
      r += get_all_files(full)
    else:
      r.append(full)
  return r


def md5(fname, bs=1024 * 1024):
  """
  Returns the MD5 checksum of the file at the given location
  """
  h = hashlib.md5()
  with open(fname, 'rb') as f:
    chunk = f.read(bs)
    while chunk:
      h.update(chunk)
      chunk = f.read(bs)
    return h.hexdigest()


def sha256(fname, bs=1024 * 1024):
  """
  Returns the SHA256 checksum of the file at the given location
  """
  h = hashlib.sha256()
  with open(fname, 'rb') as f:
    chunk = f.read(bs)
    while chunk:
      h.update(chunk)
      chunk = f.read(bs)
    return h.hexdigest()


def quick_hash_file(fname, bs=1024):
  """
  Returns a quicker hash of the file at the given location

  Collisions can happen easily, always perform a full hash in case of collision
  Warning! Changing the bs will change the value of the hash
  """
  size = os.path.getsize(fname)
  if size <= 4 * bs:
    return md5(fname, bs)
  h = hashlib.md5()
  with open(fname, 'rb') as f:
    h.update(f.read(bs))
    f.seek(size // 2, 0)
    h.update(f.read(bs))
    f.seek(-bs, 2)
    h.update(f.read(bs))
  return h.hexdigest()


def partial_hash(fname, percent=10, bs=64 * 1024):
  """
  Reads at least percent % of the file to make the hash
  """
  assert 0 < percent < 100
  size = os.path.getsize(fname)
  if size <= 3 * bs:
    return md5(fname)
  h = hashlib.md5()
  nblocks = max(1, int(percent / 100 * size / bs / 3))
  with open(fname, 'rb') as f:
    for _ in range(nblocks):
      h.update(f.read(bs))
    f.seek(int((size * (.5 - percent / 600))), 0)
    for _ in range(nblocks):
      h.update(f.read(bs))
    f.seek(-bs * nblocks, 2)
    for _ in range(nblocks):
      h.update(f.read(bs))
  return h.hexdigest()


properties = {
    'md5': md5,
    'sha256': sha256,
    'qhash': quick_hash_file,
    'phash': partial_hash,
}


def listf(loc, exclude=tuple()):
  """
  List all the files on a Local Location

  Returns a list of File objects
  """
  assert loc.is_local, "local.listf cannot be used on remote Locations"
  l = get_all_files(loc.directory)
  # TODO: real handling of exclusion (idem in remote.py)
  return [File(loc, i) for i in l if i not in exclude]


def get(prop, flist):
  """
  Compute (or get from the cache) the prop of all these local Files
  """
  assert len(set(f.loc for f in flist)) == 1, "get() can only "\
      "be used with files from a same location !"
  loc = flist[0].loc
  assert loc.is_local, "Cannot use local.get on a remote location"
  root = loc.directory

  # Managing the saved properties: try to open the files
  try:
    with open(os.path.join(
         root, f'.myrror-cached-{prop}.p'), 'rb') as sf:
      saved = pickle.load(sf)
  except FileNotFoundError:
    saved = {}

  short_prop, *index = prop.split('_')
  assert len(index) in (0, 1), "Unknown prop: " + prop
  if index:
    index = int(index[0])
    assert 0 < index < 100
  else:
    index = None
  assert short_prop in properties, "Unknown arg: " + short_prop

  t0 = time()
  # Main loop: checking if the attr exists, compute it if necessary
  # save the file every SAVE_DELAY second and prints it
  for f in flist:
    if hasattr(f, prop):
      print("Warning: Asking {prop} for {f} but it was already set!")
      continue
    af = os.path.join(root, f.path)
    if f in saved:  # The file is present in the cache
      oldsize, oldmtime, oldr = saved[f]
      if (oldsize, oldmtime) == (f.size, f.mtime):  # And up to date
        r = oldr  # We can use the old value !
      else:  # But the file was updated
        if index is None:
          r = properties[short_prop](af)  # So we recompute
        else:
          r = properties[short_prop](af, index)
        saved[f] = (f.size, f.mtime, r)  # And we save
    else:  # Not found in the cache
      if index is None:
        r = properties[short_prop](af)  # So we recompute
      else:
        r = properties[short_prop](af, index)
      saved[f] = (os.path.getsize(af), os.path.getmtime(af), r)
    t1 = time()
    if t1 - t0 > SAVE_DELAY:
      with open(os.path.join(root,
                             f'.myrror-cached-{prop}.p'), 'wb') as sf:
        pickle.dump(saved, sf)
      t0 = time()  # Not t1 ! If the saving takes time, could be blocking
    setattr(f, prop, r)
  with open(os.path.join(root, f'.myrror-cached-{prop}.p'), 'wb') as sf:
    pickle.dump(saved, sf)
  return flist


if __name__ == '__main__':
  from file import Location
  print("PERFORMING TEST")
  loc = Location("/home/vic/Vidéos/")
  lf = listf(loc)
  get("qhash", lf)
