import cmd2
import sys
import yaml
import socket
import logging
import importlib
import os
import copy
from logging import handlers

if importlib.util.find_spec("kulcli"):
  from kulcli.kul_remote import KulRemote
  from kulcli.kul_snmp_trap import KulSnmpTrapReceiver
else:
  from kul_remote import KulRemote
  from kul_snmp_trap import KulSnmpTrapReceiver

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logHandler = handlers.TimedRotatingFileHandler(filename='/var/log/kulcli.log',
                                               backupCount=35, when='midnight', interval=1, encoding='utf-8')
logHandler.setFormatter(formatter)
logHandler.suffix = "%Y%m%d"

logger = logging.getLogger('main')
logger.setLevel(logging.INFO)
logger.addHandler(logHandler)

#'10.1.160.222','10.1.160.223'
switch_list = []
def read_yaml(file_path):
  try:
    with open(file_path, "r") as f:
      return yaml.safe_load(f)
  except Exception as e:
    print(e)
    return {'switch_list': []}

def write_yaml(file_path, d):
  try:
    with open(file_path, 'w') as f:
      yaml.dump(d, f, default_flow_style=False)
  except Exception as e:
    print(e)
  

conf = read_yaml('/etc/kulcli/setting.yaml')
switch_list = conf.get('switch_list')
if switch_list == None:
  switch_list = []
vrf_list = conf.get('vrf_static_route')
file_list =[ x.split('/')[-1] for x in os.listdir('/etc/kulcli')]
kstr = KulSnmpTrapReceiver()
kstr.start()

class ConfigApp(cmd2.Cmd):
  KUL_CONFIG_CAT = "Kulcloud Controller Config List"
  crud_vrf_parser = cmd2.Cmd2ArgumentParser()
  crud_vrf_parser.add_argument("switch", choices=switch_list, help="target Switch IP")
  crud_vrf_parser.add_argument("number", type=int, help="The number of vrf list to create")

  show_vrf_parser = cmd2.Cmd2ArgumentParser()
  show_vrf_parser.add_argument("switch", choices=switch_list, help="target Switch IP")

  reg_switch_parser = cmd2.Cmd2ArgumentParser()
  reg_switch_parser.add_argument("switch",  help="target Switch IP for adding")

  unreg_switch_parser = cmd2.Cmd2ArgumentParser()
  unreg_switch_parser.add_argument("switch", choices=switch_list,  help="target Switch IP for deleting")

  create_sfc_parser = cmd2.Cmd2ArgumentParser()
  create_sfc_parser.add_argument("switch", choices=switch_list, help="target Switch IP")
  create_sfc_parser.add_argument("vrf_id",  help="Vrf Id")
  create_sfc_parser.add_argument("vlan_id", type=int, help="Vlan Id")
  create_sfc_parser.add_argument("vif_ip",  help="Vif Ip Address")
  create_sfc_parser.add_argument("prefix",  type=int, help="prefix")

  delete_sfc_parser = cmd2.Cmd2ArgumentParser()
  delete_sfc_parser.add_argument("switch", choices=switch_list, help="target Switch IP")
  delete_sfc_parser.add_argument("vlan_id", type=int, help="Vlan Id")

  add_sfc_gw_parser = cmd2.Cmd2ArgumentParser()
  add_sfc_gw_parser.add_argument("switch", choices=switch_list, help="target Switch IP")
  add_sfc_gw_parser.add_argument("vrf_id",  help="Vrf Id")
  add_sfc_gw_parser.add_argument("gateway", type=str, help="gateway IP")

  rem_sfc_gw_parser = cmd2.Cmd2ArgumentParser()
  rem_sfc_gw_parser.add_argument("switch", choices=switch_list, help="target Switch IP")
  rem_sfc_gw_parser.add_argument("vrf_id",  help="Vrf Id")

  add_sfc_rc_gw_parser = cmd2.Cmd2ArgumentParser()
  add_sfc_rc_gw_parser.add_argument("switch", choices=switch_list, help="target Switch IP")
  add_sfc_rc_gw_parser.add_argument("vlan_id", type=int, help="Vlan Id")
  add_sfc_rc_gw_parser.add_argument("vif_ip",  help="Vif Ip Address")
  add_sfc_rc_gw_parser.add_argument("prefix",  type=int, help="prefix")

  rem_sfc_rc_gw_parser = cmd2.Cmd2ArgumentParser()
  rem_sfc_rc_gw_parser.add_argument("switch", choices=switch_list, help="target Switch IP")
  rem_sfc_rc_gw_parser.add_argument("vlan_id",  help="Vlan Id")

  create_sfc_peer_parser = cmd2.Cmd2ArgumentParser()
  create_sfc_peer_parser.add_argument("switch", choices=switch_list, help="target Switch IP")
  create_sfc_peer_parser.add_argument("target_vrf_1", choices=vrf_list.keys(), help="first target vrf_name")
  create_sfc_peer_parser.add_argument("target_vrf_2", choices=vrf_list.keys(), help="second target vrf_name")

  delete_sfc_peer_parser = cmd2.Cmd2ArgumentParser()
  delete_sfc_peer_parser.add_argument("switch", choices=switch_list, help="target Switch IP")
  delete_sfc_peer_parser.add_argument("target_vrf_1", choices=vrf_list.keys(), help="first target vrf_name")
  delete_sfc_peer_parser.add_argument("target_vrf_2", choices=vrf_list.keys(), help="second target vrf_name")

  enable_link_alarm_parser = cmd2.Cmd2ArgumentParser()
  enable_link_alarm_parser.add_argument("setting", choices=["enable", "disable"], help="snmp output")

  fowarding_cmd_parser = cmd2.Cmd2ArgumentParser()
  fowarding_cmd_parser.add_argument("switch", choices=switch_list, help="target Switch IP")
  fowarding_cmd_parser.add_argument("cmd", help="cmds args")
  fowarding_cmd_parser.add_argument("commitable", choices=["enable", "disable"], help="commit cmd or not")

  scp_cmd_parser = cmd2.Cmd2ArgumentParser()
  scp_cmd_parser.add_argument("switch", choices=switch_list, help="target Switch IP")
  scp_cmd_parser.add_argument("file_name", choices=file_list, help="file name")

  get_cmd_parser = cmd2.Cmd2ArgumentParser()
  get_cmd_parser.add_argument("switch", choices=switch_list, help="target Switch IP")
  get_cmd_parser.add_argument("file_name", help="file name")

  def __init__(self):
    super().__init__()
    self.prompt = 'kulcli# '

  @cmd2.with_argparser(scp_cmd_parser)
  @cmd2.with_category(KUL_CONFIG_CAT)
  def do_send_conf(self, statement):
    """Send Config file to Switch"""
    try:
      KulRemote.scp_cmd(statement.switch, statement.file_name)
    except Exception as e:
      self.perror(e)
  
  @cmd2.with_argparser(get_cmd_parser)
  @cmd2.with_category(KUL_CONFIG_CAT)
  def do_get_conf(self, statement):
    """Get Config file to Switch"""
    try:
      filename = statement.file_name
      conf = KulRemote.get_cmd(statement.switch, filename)
      if not os.path.exists("/etc/kulcli/" + filename):
        self.poutput("Saving Conf file .. ")
        f = open("/etc/kulcli/" + filename, 'w')
        f.write(conf.replace("\r", "")) 
        f.close()
        del file_list[:]
        for x in os.listdir('/etc/kulcli'):
          file_list.append(x.split('/')[-1]) 
      else:
        raise Exception("File already exist, please change file name and retry it")
    except Exception as e:
      self.perror(e)

  @cmd2.with_category(KUL_CONFIG_CAT)
  def do_show_conf_list(self, statement):
    try:
      del file_list[:]
      for x in os.listdir('/etc/kulcli'):
        file_list.append(x.split('/')[-1]) 
      for f in file_list:
        self.poutput(f)
    except Exception as e:
      self.perror(e)


  @cmd2.with_argparser(fowarding_cmd_parser)
  @cmd2.with_category(KUL_CONFIG_CAT)
  def do_forwarding_cmd(self, statement):
    """Simple forwarding CMD"""
    try:
      commitable = True if statement.commitable == 'enable' else False
      KulRemote.direct_cmd(statement.switch, statement.cmd, commitable)
    except Exception as e:
      self.perror(e)
  
  @cmd2.with_argparser(enable_link_alarm_parser)
  @cmd2.with_category(KUL_CONFIG_CAT)
  def do_link_alarm(self, statement):
    """Enable SNMP Trap Output"""
    if statement.setting == "enable":
      kstr.snmp_enable()
    else:
      kstr.snmp_disable()
  
  @cmd2.with_category(KUL_CONFIG_CAT)
  def do_show_link_alarm(self, statement):
    """Show SNMP Trap Output Setting"""
    output = 'enabled' if kstr.enable else 'disabled'
    self.poutput(output)

  @cmd2.with_argparser(create_sfc_peer_parser)
  @cmd2.with_category(KUL_CONFIG_CAT)
  def do_create_sfc_peer(self, statement):
    """Create Service Function Chain Peer"""
    try:
      KulRemote.create_sfc_peer(
        statement.switch, 
        vrf_list[statement.target_vrf_1]['route'],
        vrf_list[statement.target_vrf_1]['next_hop'],
        vrf_list[statement.target_vrf_2]['route'],
        vrf_list[statement.target_vrf_2]['next_hop'],
      )
    except Exception as e:
      self.perror(e)

  @cmd2.with_argparser(delete_sfc_peer_parser)
  @cmd2.with_category(KUL_CONFIG_CAT)
  def do_delete_sfc_peer(self, statement):
    """Delete Service Function Chain Peer"""
    try:
      KulRemote.delete_sfc_peer(
        statement.switch, 
        vrf_list[statement.target_vrf_1]['route'],
        vrf_list[statement.target_vrf_2]['route'],
      )
    except Exception as e:
      self.perror(e)

  @cmd2.with_category(KUL_CONFIG_CAT)
  def do_show_sfc_peer(self, statement):
    """Add Service Function Chain Recieve gateway"""
    try:
      self.poutput(vrf_list)
    except Exception as e:
      self.perror(e)

  @cmd2.with_argparser(add_sfc_rc_gw_parser)
  @cmd2.with_category(KUL_CONFIG_CAT)
  def do_add_sfc_receive_gateway(self, statement):
    """Add Service Function Chain Recieve gateway"""
    try:
      KulRemote.add_sfc_receive_gateway(
        statement.switch, 
        statement.vlan_id, 
        statement.vif_ip, 
        statement.prefix
      )
    except Exception as e:
      self.perror(e)
  
  @cmd2.with_argparser(rem_sfc_rc_gw_parser)
  @cmd2.with_category(KUL_CONFIG_CAT)
  def do_remove_sfc_receive_gateway(self, statement):
    """Remove Service Function Chain Recieve gateway"""
    try:
      KulRemote.remove_sfc_receive_gateway(statement.switch, statement.vlan_id)
    except Exception as e:
      self.perror(e)

  @cmd2.with_argparser(add_sfc_gw_parser)
  @cmd2.with_category(KUL_CONFIG_CAT)
  def do_add_sfc_gateway(self, statement):
    """Add Service Function Chain gateway"""
    try:
      KulRemote.add_sfc_gateway(statement.switch, statement.vrf_id, statement.gateway)
    except Exception as e:
      self.perror(e)
  
  @cmd2.with_argparser(rem_sfc_gw_parser)
  @cmd2.with_category(KUL_CONFIG_CAT)
  def do_remove_sfc_gateway(self, statement):
    """Remove Service Function Chain gateway"""
    try:
      KulRemote.remove_sfc_gateway(statement.switch, statement.vrf_id)
    except Exception as e:
      self.perror(e)
    
  @cmd2.with_argparser(create_sfc_parser)
  @cmd2.with_category(KUL_CONFIG_CAT)
  def do_create_sfc(self, statement):
    """Make service Function Chain"""
    try:
      print ("%s %s" %(statement.switch, statement.vrf_id))
      KulRemote.create_sfc(
        statement.switch, 
        statement.vrf_id, 
        statement.vlan_id, 
        statement.vif_ip, 
        statement.prefix
      )
    except Exception as e:
      self.perror(e)
  
  @cmd2.with_argparser(delete_sfc_parser)
  @cmd2.with_category(KUL_CONFIG_CAT)
  def do_delete_sfc(self, statement):
    """Make service Function Chain"""
    try:
      KulRemote.delete_sfc(statement.switch, statement.vlan_id)
    except Exception as e:
      self.perror(e)

  @cmd2.with_argparser(crud_vrf_parser)
  @cmd2.with_category(KUL_CONFIG_CAT)
  def do_create_vrf(self, statement):
    """Create Vrf for specific Switch"""
    self.poutput("create vrf on switch : " + statement.switch)
    number = statement.number
    if 1 <= number and number <= 512:
      KulRemote.create_vrf(statement.switch, number)
    else:
      self.perror("error the number is out of range")
      
  @cmd2.with_argparser(crud_vrf_parser)
  @cmd2.with_category(KUL_CONFIG_CAT)
  def do_delete_vrf(self, statement):
    """Delete Vrf for specific Switch"""
    self.poutput("delete vrf on switch : " + statement.switch)
    number = statement.number
    if 1 <= number and number <= 512:
      KulRemote.delete_vrf(statement.switch, number)
    else:
      self.perror("error the number is out of range")
  
  @cmd2.with_argparser(show_vrf_parser)
  @cmd2.with_category(KUL_CONFIG_CAT)
  def do_show_vrf(self, statement):
    """Show Vrf for specific Switch"""
    try:
      vrf_list = KulRemote.show_vrf(statement.switch)
      self.ppaged(vrf_list)
    except Exception as e:
      self.perror(e)

  
  @cmd2.with_category(KUL_CONFIG_CAT)
  def do_show_switch(self, statement):
    """Show Switches"""
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

  @cmd2.with_argparser(reg_switch_parser)
  @cmd2.with_category(KUL_CONFIG_CAT)
  def do_register_switch(self, statement):
    """Register a Switch"""
    try:
      socket.inet_aton(statement.switch)
      for swi in switch_list:
        if swi == statement.switch:
          raise Exception("switch %s is already registered" %(statement.switch))
      switch_list.append(statement.switch)
      conf['switch_list'] = switch_list
      write_yaml('/etc/kulcli/setting.yaml', conf)
    except Exception as e:
      self.perror(e)
      

  @cmd2.with_argparser(unreg_switch_parser)
  @cmd2.with_category(KUL_CONFIG_CAT)
  def do_unregister_switch(self, statement):
    """Unregister a Switch"""
    try:
      socket.inet_aton(statement.switch)
      switch_list.remove(statement.switch)
      conf['switch_list'] = switch_list
      write_yaml('/etc/kulcli/setting.yaml', conf)
    except:
      self.perror("no switch %s "%(statement.switch))

def main():
  app = ConfigApp()
  try:
    ret = app.cmdloop()
    kstr.stop()
  except KeyboardInterrupt:
    sys.exit()

if __name__ == "__main__":
  main()