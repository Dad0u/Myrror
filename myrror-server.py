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
  assert len(sys.argv) == 3,"Invalid command"
  if sys.argv[1] == "list":
    root = sys.argv[2]
    for fullpath in get_all_files(root):
      print(f"#n>{os.path.relpath(fullpath,root)}")
      print(f"#s>{os.path.getsize(fullpath)}")
      print(f"#t>{os.path.getmtime(fullpath)}")
  elif sys.argv[1].startswith('get_'):
    # Get the % of phash if necessary
    prop,*index = sys.argv[1][4:].split('_')
    assert len(index) in (0,1),"Unknown command: "+sys.argv[1]
    if index:
      index = int(index[0])
      assert 0 < index < 100
    assert prop in properties,"Unknown arg: "+prop
    lfile = sys.argv[2]
    with open(lfile,'r') as f:
      flist = f.readlines()
    for f in flist:
      if prop == 'phash':
        print(index)
        print(f'#p>{properties[prop](f[:-1],index)}')
      else:
        print(f'#p>{properties[prop](f[:-1])}')
  else:
    raise NameError("Unknown command: "+sys.argv[1])
