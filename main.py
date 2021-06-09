def sync(src: str, dst: str, diff=None):
  """
  Used to sync src and dst

  If diff is given, the comparison is skipped
  Then, the operations will be performed to make dst identical to src
  """


def compare(src: str, dst: str):
  """
  Will compare src and dst, a report will be printed

  This will print the files only on src, the files only on dst,
  the files once on both but with a diffrent name/path and finally the groups
  of files both on src and dst that do not fall in the previous categories
  SRC_ONLY:
    The files only on src (to be copied)
  DST_ONYL:
    The files only on dst (to be deleted/archived)
  MOVED:
    The files once on both sides but renamed (to be moved)
  GROUPS:
    The files with one or more copies on both sides (to be moved,
      deleted or locally copied on dst depending on the number of copies)
  """


def export(src: str, dst: str, diff=None):
  """
  Will print the actions to be executed to make dst identical to src

  If diff is specified (filename or dict), the actions are
  SEND:
    Files only on src, they must be sent to dst
  RM:
    Files only on dst, can be deleted
  CP:
    Files already on dst but with a lower count on src than dst
  MV:
    Files already on dst but needing to be renamed/moved
  """


commands = {
    'sync': sync,
    'compare': compare,
    'export': export,
}


if __name__ == "__main__":
  import sys
  cmd, *attrs = sys.argv[1:]
