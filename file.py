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
    return user, host, directory

  @property
  def remote(self):
    return self.host is not None

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
    if self.loc.remote:
      return f"Remote file on <{self.loc.host}>: #{self.loc.directory}#{self.path}"
    return f"Local file: #{self.loc.directory}#{self.path}"
