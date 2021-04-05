import subprocess

host = "zeropi.home"
path = "/home/vic/hdd/raid/Musique/Santiano"


class F:
  def __init__(self,path,size,mtime):
    self.path = path
    self.size = size
    self.mtime = mtime

  def __repr__(self):
    return self.path


def str_to_files(s):
  lines = s.split('\n')
  r = []
  current = 2
  d = {"name":"#n>","size":"#s>","mtime":"#t>"}
  dl = ['name','size','mtime']
  s = {}
  for line in lines:
    current = (current + 1)%3
    if not line.startswith(d[dl[current]]):
      if line:
        print("Ignored line:\n",line)
      continue
    else:
      s[dl[current]] = line[3:]
    if current == 2:
      r.append(F(s['name'],s['size'],s['mtime']))
  return r


p = subprocess.run(
    f'ssh {host} python3 < myrror-server.py - list "{path}"',
    shell=True,capture_output=True,encoding='utf-8')
r = str_to_files(p.stdout)

print(len(r))
for f in r:
  print(f)

with open('test.txt','w') as fi:
  fi.write(path+'\n')
  for f in r:
    fi.write(f.path+"\n")
subprocess.run(f'scp -C test.txt {host}:{path}/.myrror-toupdate.txt',shell=True)
p = subprocess.run(f'ssh {host} python3 < myrror-server.py - get_qhash {path}/.myrror-toupdate.txt',
    shell=True,capture_output=True,encoding='utf-8')
print(p.stdout)
subprocess.run(f'ssh {host} rm {path}/.myrror-toupdate.txt',shell=True)
