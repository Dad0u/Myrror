import os
import hashlib


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
    return h.hexdigest()


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
    return h.hexdigest()


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
  return h.hexdigest()


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
  return h.hexdigest()


properties = {
    'md5':md5,
    'sha256':sha256,
    'qhash':quick_hash_file,
    'phash':partial_hash,
  }


if __name__ == '__main__':
  import sys
  SAVE_DELAY = 60 # When reading properties, save them every X seconds
  assert len(sys.argv) == 3,"Invalid command"
  if sys.argv[1] == "list":
    root = sys.argv[2]
    for fullpath in get_all_files(root):
      print(f"#n>{os.path.relpath(fullpath,root)}")
      print(f"#s>{os.path.getsize(fullpath)}")
      print(f"#t>{os.path.getmtime(fullpath)}")
  elif sys.argv[1].startswith('get_'):
    import pickle
    from time import time
    # Get the % of phash if necessary
    prop,*index = sys.argv[1][4:].split('_')
    assert len(index) in (0,1),"Unknown command: "+sys.argv[1]
    if index:
      index = int(index[0])
      assert 0 < index < 100
    else:
      index = None
    assert prop in properties,"Unknown arg: "+prop
    lfile = sys.argv[2]

    long_prop = prop if not index else f'{prop}_{index}'
    # Managing the saved properties: try to open the files
    with open(lfile,'r') as f:
      root,*flist = [l[:-1] for l in f.readlines()]
    try:
      with open(os.path.join(root,f'.myrror-cached-{long_prop}.p'),'rb') as sf:
        saved = pickle.load(sf)
    except FileNotFoundError:
      saved = {}

    t0 = time()
    # Main loop: checking if the attr exists, compute it if necessary
    # save the file every SAVE_DELAY second and prints it
    for f in flist:
      if f in saved:
        oldsize,oldmtime,oldr = saved[f]
        size,mtime = os.path.getsize(f),os.path.getmtime(f)
        if (oldsize,oldmtime) == (size,mtime):
          r = oldr
        else:
          r = properties[prop](f)
          saved[f] = (size,mtime,r)
      else:
        r = properties[prop](f)
        saved[f] = (os.path.getsize(f),os.path.getmtime(f),r)
      t1 = time()
      if t1 - t0 > SAVE_DELAY:
        with open(os.path.join(root,
          f'.myrror-cached-{long_prop}.p'),'w') as sf:
          pickle.dump(saved,sf)
        t0 = t1
      print(f'#p>{r}')
    with open(os.path.join(root, f'.myrror-cached-{long_prop}.p'),'wb') as sf:
      pickle.dump(saved,sf)
  else:
    raise NameError("Unknown command: "+sys.argv[1])
