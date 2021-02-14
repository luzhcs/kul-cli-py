import cmd2
import sys
from kul_remote import KulRemote


#switch_list = ['172.16.110.2', '172.16.110.3']
switch_list = ['10.1.160.222','10.1.160.223']

'''
[summary]
set ip_addr [lindex $argv 0];
send_user "\nDevice: admin@$ip_addr.\n"
spawn ssh admin@$ip_addr
expect "password:"
send "kulpass@123\r"
expect ">"
send "configure\r"
expect "#"
log_user 1
for {set x 0} {$x<128} {incr x} {
    send "set ip vrf test$x description test$x\r"
    expect "#"
}
send "commit\r"
send "q\r"
send "q\r"
send "q\r"

expect eof
'''

class ConfigApp(cmd2.Cmd):
  KUL_CONFIG_CAT = "Kulcloud Controller Config List"
  crud_vrf_parser = cmd2.Cmd2ArgumentParser()
  crud_vrf_parser.add_argument("switch", choices=switch_list, help="target Switch IP")
  crud_vrf_parser.add_argument("number", type=int, help="The number of vrf list to create")

  show_vrf_parser = cmd2.Cmd2ArgumentParser()
  show_vrf_parser.add_argument("switch", choices=switch_list, help="target Switch IP")

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
    pass
  

if __name__ == "__main__":
    app = ConfigApp()
    sys.exit(app.cmdloop())