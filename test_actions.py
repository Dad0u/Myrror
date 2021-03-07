from myrror import get_actions


class T:
  def __init__(self,rel_path):
    self.rel_path = rel_path

  def __repr__(self):
    return self.rel_path


a = get_actions([([T("A"),T("G")],[T("B")]), ([T("B")],[T("A")]), ([T("C")],[T("E")]), ([T("D")],[]),([],[T("F")]), ([T("H"), T("I")],[])])

print(a)
