import os
import shutil

from file import File

TRASHDIR = "TRASH"


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


def logical_or(funcs):
  """
  Chains the funcs
  """
  def f(*args):
    for f in funcs:
      if f(*args):
        return True
    return False
  return f


def match(l,comp):
  """
  Takes a list of File objects and groups them

  This func implicitely compares the size (different sizes cannot match)
  comp is a function or list of functions. They will ALL be called until True
  is returned (logical OR). If they all return False, the files are considered
  different
  Returns a list of list, each sublist containing matching files

  UNDEFINED BEHAVIOR IN CASE OF GROUPS WITH NON-MATCHING FILES
  ie A = B, B = C and A != C. One of these (in)equality will be ignored
  and return one of the following [(a,b,c)], [(a,b),(c)], [(a),(b,c)]
  """
  r = []
  d = {}
  if isinstance(comp,list):
    comp = logical_or(comp)
  for f in l:
    if f.size in d:
      d[f.size].append(f)
    else:
      d[f.size] = [f]
  for size_group in d.values():
    l = list(size_group)
    while l:
      if len(l) == 1:
        r.append(l)
        break
      temp_r = [l[0]]
      for f in l[1:]:
        if comp(l[0],f):
          temp_r.append(f)
      for f in temp_r:
        l.remove(f)
      r.append(temp_r)
  return r


def find_file(f,l,complist):
  l = [fl for fl in l if fl.size == f.size]
  for comp in complist:
    for fl in list(l):
      if not comp(fl,f):
        l.remove(fl)
  return l


def compare(f1,f2,attr):
  return getattr(f1,attr) == getattr(f2,attr)


def same_name(f1,f2):
  """
  Enough to avoid computing the hash
  """
  for attr in ("rel_path","size","mtime"):
    if not compare(f1,f2,attr):
      return False
  return True


def same_content(f1,f2):
  for attr in ("size","qhash","partial_hash"):
    if not compare(f1,f2,attr):
      return False
  return True


def comp_func(attr):
  def f(f1,f2):
    return getattr(f1,attr) == getattr(f1,attr)
  return f


def temp_name(f):
  if os.path.exists(f):
    return os.path.join(os.path.dirname(f),'TMPMYR_'+os.path.basename(f))
  return f


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
  # path+nom+taille+datemodif OU taille+qhash+partial_hash
  # Keep the original list (will be used for local copies)
  #full_dst_list = list(dst_list)
  # 1st pass: removing files with same Path, name, size and modified date
  #dst_path_dict = {f.rel_path:f for f in dst_list}
  #for f in list(src_list):
  #  if f.rel_path in dst_path_dict:
  #    f_dst = dst_path_dict[f.rel_path]
  #    #if f.size == f_dst.size and f.mtime == f_dst.mtime:
  #    if same_name(f,f_dst):
  #      src_list.remove(f)
  #      dst_list.remove(f_dst)
  #print(f"Ignoring {len(full_dst_list) - len(dst_list)} "
#"files with same path, name, size and date")
  # Now, all the files in src_list must go to dst
  groups = match(src_list+dst_list,[same_name,same_content])
  # Now let's split each group into a pair (src,dst)
  src_only,both,dst_only = [],[],[]
  for g in groups:
    sg = [f for f in g if f.root == src]
    dg = [f for f in g if f.root == dst]
    if sg:
      if dg:
        # Remove the matching groups
        if set([f.rel_path for f in sg]) != set([f.rel_path for f in dg]):
          both.append((sg,dg))
      else:
        src_only.append(sg)
    else:
      dst_only.extend(dg)

  action = {}
  action['rm'] = []
  action['mv'] = []
  action['local_cp'] = []
  action['remote_cp'] = []
  action['final_mv'] = []

  for s,d in both:
    for i in list(s):
      if i.rel_path in [f.rel_path for f in d] and len(d) > 1:
        s.remove(i)
        d.remove([f for f in d if f.rel_path == i.rel_path][0])

  for f in dst_only:
    action['rm'].append(f.rel_path)
  for s,d in both:
    for i,j in zip(s,d):
      action['mv'].append((j.rel_path,i.rel_path))
      #action['mv'].append((j.rel_path,temp_name(i.rel_path)))
      #if temp_name(i.rel_path) != i.rel_path:
      #  action['final_mv'].append((temp_name(i.rel_path),i.rel_path))
    diff = len(s)-len(d)
    if diff > 0:
      for i in s[diff:]:
        action['local_cp'].append((d[0].rel_path,temp_name(i.rel_path)))
    elif diff < 0:
      for i in d[diff:]:
        action['rm'].append(i.rel_path)
  for l in src_only:
    action["remote_cp"].append(l[0].rel_path)
    for f in l[1:]:
      action["local_cp"].append((l[0].rel_path,f.rel_path))

  # Last part: make all the moves/copies in temp files or separate dir
  # execute everything, the move then to final name
  # And finally handle the dirs (remove empty dirs on dst)
  print(action)
  if input('Proceed? (y/[n])').lower() != 'y':
    raise KeyboardInterrupt

  def my_rm(f):
    d = os.path.join(TRASHDIR,os.path.basename(f))
    i = 1
    while os.path.exists(d):
      name,ext = os.path.splitext(os.path.basename(f))
      fname = name+"_{:03d}".format(i)+ext
      d = os.path.join(TRASHDIR,fname)
      i += 1
    shutil.move(f,d)
  os.makedirs(TRASHDIR,exist_ok=True)

  for f in action['remote_cp']:
    print("remote CP",f)
    d = os.path.join(dst,f)
    os.makedirs(os.path.dirname(d),exist_ok=True)
    if temp_name(d) != d:
      action['final_mv'].append((temp_name(d),d))
    shutil.copy2(os.path.join(src,f),temp_name(d))

  for f1,f2 in action['local_cp']:
    print("local CP",f1,f2)
    d = os.path.join(dst,f2)
    os.makedirs(os.path.dirname(d),exist_ok=True)
    if temp_name(d) != d:
      action['final_mv'].append((temp_name(d),d))
    shutil.copy2(os.path.join(dst,f1),temp_name(d))

  for f1,f2 in action['mv']:
    print("MV",f1,f2)
    d = os.path.join(dst,f2)
    os.makedirs(os.path.dirname(d),exist_ok=True)
    if temp_name(d) != d:
      action['final_mv'].append((temp_name(d),d))
    shutil.move(os.path.join(dst,f1),temp_name(d))

  for f in action['rm']:
    print("RM",f)
    #shutil.move(os.path.join(dst,f),TRASHDIR)
    my_rm(os.path.join(dst,f))

  for f1,f2 in action['final_mv']:
    print("MV",f1,f2)
    os.makedirs(os.path.dirname(os.path.join(dst,f2)),exist_ok=True)
    shutil.move(os.path.join(dst,f1),os.path.join(dst,f2))
