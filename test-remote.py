import subprocess

host = "localhost"
path = "/home/vic/projects/config/"

subprocess.run(f'rsync -avu myrror-server.py {host}:{path}',shell=True)
subprocess.run(f'rsync -avu file.py {host}:{path}',shell=True)
p = subprocess.run(f'ssh {host} "cd {path} && python3 myrror-server.py list {path}"',shell=True,capture_output=True,encoding='utf-8')


class F:
  def __init__(self,path,size,mtime):
    self.path = path
    self.size = size
    self.mtime = mtime


def str_to_files(s):
  l = s.split('\n')
  r = []
  for path,size,mtime in zip(l[::3],l[1::3],l[2::3]):
    r.append(F(path,size,mtime))
  return r
