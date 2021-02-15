import cmd2
import sys
import yaml
import socket
from kul_remote import KulRemote

#'10.1.160.222','10.1.160.223'
switch_list = []
def read_yaml(file_path):
  with open(file_path, "r") as f:
    return yaml.safe_load(f)

def write_yaml(file_path, d):
  with open(file_path, 'w') as f:
    yaml.dump(d, f, default_flow_style=False)

conf = read_yaml('setting.yaml')
switch_list = conf.get('switch_list')

class ConfigApp(cmd2.Cmd):
  KUL_CONFIG_CAT = "Kulcloud Controller Config List"
  crud_vrf_parser = cmd2.Cmd2ArgumentParser()
  crud_vrf_parser.add_argument("switch", choices=switch_list, help="target Switch IP")
  crud_vrf_parser.add_argument("number", type=int, help="The number of vrf list to create")

  show_vrf_parser = cmd2.Cmd2ArgumentParser()
  show_vrf_parser.add_argument("switch", choices=switch_list, help="target Switch IP")

  crud_switch_parser = cmd2.Cmd2ArgumentParser()
  crud_switch_parser.add_argument("switch",  help="target Switch IP for adding")

  def __init__(self):
    super().__init__()
    self.prompt = 'kul-app# '
    
  @cmd2.with_category(KUL_CONFIG_CAT)
  def do_make_sfc(self, statement):
    for arg in statement.arg_list:
      self.poutput(arg)

  @cmd2.with_argparser(crud_vrf_parser)
  @cmd2.with_category(KUL_CONFIG_CAT)
  def do_create_vrf(self, statement):
    self.poutput("create vrf on switch : " + statement.switch)
    number = statement.number
    if 1 <= number and number <= 512:
      KulRemote.create_vrf(statement.switch, number)
    else:
      self.perror("error the number is out of range")
      
  @cmd2.with_argparser(crud_vrf_parser)
  @cmd2.with_category(KUL_CONFIG_CAT)
  def do_delete_vrf(self, statement):
    self.poutput("delete vrf on switch : " + statement.switch)
    number = statement.number
    if 1 <= number and number <= 512:
      KulRemote.delete_vrf(statement.switch, number)
    else:
      self.perror("error the number is out of range")
  
  @cmd2.with_argparser(show_vrf_parser)
  @cmd2.with_category(KUL_CONFIG_CAT)
  def do_show_vrf(self, statement):
    vrf_list = KulRemote.show_vrf(statement.switch)
    self.ppaged(vrf_list)
  
  @cmd2.with_category(KUL_CONFIG_CAT)
  def do_show_switch(self, statement):
    self.poutput("Waiting for Checking Switch Status")
    template = "{0:12}|{1:12}|{2:12}" 
    out = ""
    out += template.format("Switch addr", "Switch Name", "Status") + "\n"
    out += "================================" + "\n"
    for swi in switch_list:
      try:
        name = KulRemote.get_switch_name(swi)
        out += template.format(swi,name,'Ok') + "\n"
      except Exception as e:
        name = 'Not found'
        out += template.format(swi,name,'Not Ok') + "\n"
    out += "================================" + "\n"
    self.poutput(out)

  @cmd2.with_argparser(crud_switch_parser)
  @cmd2.with_category(KUL_CONFIG_CAT)
  def do_register_switch(self, statement):
    try:
      socket.inet_aton(statement.switch)
      for swi in switch_list:
        if swi == statement.switch:
          raise Exception("switch %s is already registered" %(statement.switch))
      switch_list.append(statement.switch)
      conf['switch_list'] = switch_list
      write_yaml('setting.yaml', conf)
    except Exception as e:
      self.perror(e)
      

  @cmd2.with_argparser(crud_switch_parser)
  @cmd2.with_category(KUL_CONFIG_CAT)
  def do_unregister_switch(self, statement):
    try:
      socket.inet_aton(statement.switch)
      switch_list.remove(statement.switch)
      conf['switch_list'] = switch_list
      write_yaml('setting.yaml', conf)
    except:
      self.perror("no switch %s "%(statement.switch))

if __name__ == "__main__":
  app = ConfigApp()
  sys.exit(app.cmdloop())