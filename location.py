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
