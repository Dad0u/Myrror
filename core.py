from file import File, Location
import remote
import local


def listf(loc: Location, exclude=tuple()):
  """
  Returns a list of File objects in the Location

  Works with either local or remote Locations
  """
  if loc.is_local:
    return local.listf(loc, exclude)
  # else:
  return remote.listf(loc, exclude)


def get(prop: str, flist: list[File]):
  """
  Get a property in a list of files

  Does not return anything ! The files are updated in place
  """
  s = set()
  for f in flist:
    s.add(f.loc)
  if not s:
    return
  if len(s) != 1:
    raise AttributeError("Can only call get() on a list of files "
          "from the same location")
  # Only get the prop of the files that need it !
  flist = [f for f in flist if not hasattr(f, prop)]
  if flist:
    if s.pop().is_local:
      local.get(prop, flist)
    else:
      remote.get(prop, flist)
