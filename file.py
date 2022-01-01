import os


class Location:
  """
  Represents a directory either local or remote

  Takes a string to init
  A local Location is simply defined by the path (absolute or relative)
  A remote location is written [user@]host:directory
  The user, host and directory attribute will be parsed
  """
  def __init__(self, location_str: str):
    self.location_str = location_str
    self.user, self.host, self.directory = self.parse_location(location_str)

  @staticmethod
  def parse_location(location_str: str):
    if ":" in location_str:
      user_host, *directory = location_str.split(':')
      if "@" in user_host:
        try:
          user, host = user_host.split('@')
        except ValueError:
          print("Unexpected syntax: @ in username or host")
          raise
      else:
        user = None
        host = user_host
      directory = ':'.join(directory)
    else:
      user = host = None
      directory = location_str
    while directory.endswith('/'):
      directory = directory[:-1]
    return user, host, directory

  @property
  def is_remote(self):
    return self.host is not None

  @property
  def is_local(self):
    return self.host is None

  def __eq__(self, l2):
    if self.is_local:
      return l2.is_local and self.directory == l2.directory
    return self.user, self.host, self.directory == \
        l2.user, l2.host, l2.directory

  def __hash__(self):
    return hash((self.user, self.host, self.directory))


class File:
  """
  Represents a file

  It has a base location, a directory and a name
  """
  def __init__(self, loc: Location, path: str):
    self.loc = loc
    self.dir, self.name = os.path.split(path)
    self.path = path

  def __repr__(self):
    if self.loc.is_remote:
      return f"Remote file on <{self.loc.host}:{self.loc.directory}>"\
             f" {self.path}"
    return f"Local file: {self.loc.directory}#{self.path}"

  def __eq__(self, f2):
    return (self.loc, self.path) == (f2.loc, f2.path)

  def __hash__(self):
    return hash((self.loc, self.path))
