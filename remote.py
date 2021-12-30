import subprocess
import os

from file import File

TMP = '.myrror-tmp.txt'


def str_to_files(s):
  lines = s.split('\n')
  r = []
  current = 0
  d = {"path": "#n>", "size": "#s>", "mtime": "#t>"}
  dl = ['path', 'size', 'mtime']
  s = {}
  for line in lines:
    if not line.startswith(d[dl[current]]):
      if line:
        print("Ignored line:\n" + line)
      continue
    s[dl[current]] = line[3:]
    current = (current + 1) % 3
    if current == 0:
      r.append(dict(s))
  return r


def str_to_prop(s):
  lines = s.split('\n')
  r = []
  for line in lines:
    if not line.startswith("#p>"):
      if line:
        print("Ignored line:\n", line)
      continue
    r.append(line[3:])
  return r


def listf(location, exclude=tuple()):
  """
  List all the files on a remote Location

  Returns a list of File objects
  """
  assert location.is_remote, "remote.listf cannot be used on local Locations"
  p = subprocess.run(
      f'ssh {location.host} python3 < '
      f'myrror-server.py - list "{location.directory}"',
      shell=True, capture_output=True, encoding='utf-8', check=True)
  # print("DEBUG", p.stdout)
  rd = str_to_files(p.stdout)
  # TODO: real handling of exclusion (idem in local.py)
  r = [File(location, f['path']) for f in rd
       if not any(e in f['path'] for e in exclude)]
  for f, d in zip(r, rd):
    f.size = int(d['size'])
    f.mtime = int(d['mtime'])
  return r


def get(prop, flist):
  """
  Compute (or get from the cache) the prop of all these remote Files
  """
  assert len(set(f.loc for f in flist)) == 1, "get() can only "\
      "be used with files from a same location !"
  loc = flist[0].loc
  assert loc.is_remote, "Cannot use remote.get on a local Location"
  with open(TMP, 'w') as fi:
    fi.write(loc.directory + '\n')
    for f in flist:
      fi.write(f.path + "\n")
  subprocess.run(
      f'scp -C {TMP} {loc.host}:{loc.directory}/.myrror-toupdate.txt',
      shell=True, check=True)
  os.remove(TMP)
  p = subprocess.run(f'ssh {loc.host} python3 < myrror-server.py - '
                     f'get_{prop} "{loc.directory}/.myrror-toupdate.txt"',
                     shell=True, capture_output=True, encoding='utf-8',
                     check=True)
  subprocess.run(f'ssh {loc.host} rm {loc.directory}/.myrror-toupdate.txt',
                 shell=True, check=True)
  r = str_to_prop(p.stdout)
  assert len(r) == len(flist), "Failed getting properties of the files!"
  for f, p in zip(flist, r):
    setattr(f, prop, p)


if __name__ == '__main__':
  from file import Location
  print("PERFORMING TEST")
  # host = "raspi0.dadou.ovh"
  # path = "/home/vic/hdd/raid/Pictures/Divers"
  host = "localhost"
  path = "/home/vic/Vidéos"
  loc = Location(f"{host}:{path}")
  l = listf(loc)
  # l.append(File(loc, 'inexistant_file'))
  print(get('phash_5', l))
