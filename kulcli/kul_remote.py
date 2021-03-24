import pexpect
import sys
import time
import socket
import struct


def ip2int(addr):
    return struct.unpack("!I", socket.inet_aton(addr))[0]

def int2ip(addr):
    return socket.inet_ntoa(struct.pack("!I", addr))

def try_login(target_switch):
    #print("Try login")
    child = pexpect.spawn('ssh -p 2203 admin@' + target_switch, encoding='utf-8', timeout=3)
    password = child.expect(["password:", "yes/no"])
    if password == 0:
        child.sendline("Ismart123!")
        child.expect(">")
    elif password == 1:
        child.sendline("yes")
        child.expect("password:")
        child.sendline("Ismart123!")
        child.expect(">")
    return child

class KulRemote:
    def __init__(self):
        pass

    @staticmethod
    def scp_cmd(target_switch: str, file_name: str):
        cmd = 'scp -P 2203 ' + '/etc/kulcli/' + file_name + ' admin@' + target_switch + ":~"
        child = pexpect.spawn(cmd)
        i = child.expect(["password:", pexpect.EOF])
        if i==0: # send password                
            child.sendline("Ismart123!")
            child.expect(pexpect.EOF)
        elif i==1: 
            print ("Got the key or connection timeout")
            pass
        child = try_login(target_switch)
        #child.logfile = sys.stdout
        child.sendline("configure")
        child.expect("#")
        child.sendline("load override " + file_name)
        child.expect("#")
        child.sendline("commit")
        child.expect("#")
        ex = child.expect(["Commit OK", "Commit failed"])
        if ex == 1:
            raise Exception("commit failed")
        else:
            print("Commit Complete.")

    @staticmethod
    def get_cmd(target_switch: str, file_name: str):
        child = try_login(target_switch)
        #child.logfile = sys.stdout
        child.sendline("configure")
        child.expect("#")
        cmd = "show all | no-more"
        child.sendline(cmd)
        child.expect("no-more")
        child.expect("admin@")
        conf = child.before
        #conf = child.before.replace('^M','')
        return conf


    @staticmethod
    def direct_cmd(target_switch: str, cmd: str, commitable: bool):
        child = try_login(target_switch)
        child.sendline("configure")
        #child.logfile = sys.stdout
        child.expect("#")
        child.sendline(cmd)
        child.expect(".*@*#")
        child.expect("admin@")
        if commitable == True:
            child.sendline("commit")
            child.expect("#")
            ex = child.expect(["Commit OK", "Commit failed"])
            if ex == 1:
                raise Exception("commit failed")
            else:
                print("Commit Complete.")
        else:
            print(child.before)

    @staticmethod
    def create_sfc_peer(
            target_switch: str,
            target_vrf_1_route: str, 
            target_vrf_1_nh: str, 
            target_vrf_2_route: str, 
            target_vrf_2_nh: str
        ):
        child = try_login(target_switch)
        child.sendline("configure")
        child.expect("#")
        cmd = "set protocols static route %s next-hop %s" %(target_vrf_1_route, target_vrf_1_nh)
        child.sendline(cmd)
        child.expect("#")
        cmd = "set protocols static route %s next-hop %s" %(target_vrf_2_route, target_vrf_2_nh)
        child.sendline(cmd)
        child.expect("#")
        child.sendline("commit")
        child.expect("#")
        ex = child.expect(["Commit OK","Commit failed"])
        if ex == 1:
            raise Exception("commit failed")
        else:
            print("Added.")

    @staticmethod
    def delete_sfc_peer(
            target_switch: str,
            target_vrf_1_route: str, 
            target_vrf_2_route: str
        ):
        child = try_login(target_switch)
        child.sendline("configure")
        child.expect("#")
        cmd = "delete protocols static route %s" %(target_vrf_1_route)
        child.sendline(cmd)
        ex = child.expect(["Deleting", "syntax error"])
        if ex == 1:
            raise Exception("systax error")
        cmd = "delete protocols static route %s" %(target_vrf_2_route)
        child.sendline(cmd)
        ex = child.expect(["Deleting", "syntax error"])
        if ex == 1:
            raise Exception("systax error")
        child.sendline("commit")
        child.expect("#")
        ex = child.expect(["Commit OK","Commit failed"])
        if ex == 1:
            raise Exception("commit failed")
        else:
            print("Deleted.")

    #- set vlan-interface interface vlan27 vif vlan27 address 192.168.1.1 prefix-length 24
    #- set vlans vlan-id 27 l3-interface vlan27
    #- commit
    # vif vlan id alter
    @staticmethod
    def add_sfc_receive_gateway(target_switch: str, vlan_id: int, vif_ip: str, prefix: int):
        child = try_login(target_switch)
        child.sendline("configure")
        child.expect("#")
        cmd = "set vlan-interface interface vlan%s vif vlan%s address %s prefix-length %s" %(str(vlan_id), str(vlan_id), vif_ip, str(prefix))
        child.sendline(cmd)
        child.expect("#")
        cmd = "set vlans vlan-id %s l3-interface \"vlan%s\"" %(str(vlan_id), str(vlan_id))
        child.sendline(cmd)
        child.expect("#")
        child.sendline("commit")
        child.expect("#")
        ex = child.expect(["Commit OK","Commit failed"])
        if ex == 1:
            raise Exception("commit failed")
        else:
            print("Added.")

    @staticmethod
    def remove_sfc_receive_gateway(target_switch: str, vlan_id: int):
        child = try_login(target_switch)
        child.sendline("configure")
        child.expect("#")
        cmd = "delete vlan-interface interface vlan%s" %(str(vlan_id))
        child.sendline(cmd)
        ex = child.expect(["Deleting", "syntax error"])
        if ex == 1:
            raise Exception("systax error")
        cmd = "delete vlans vlan-id %s" %(str(vlan_id))
        child.sendline(cmd)
        ex = child.expect(["Deleting", "syntax error"])
        if ex == 1:
            raise Exception("systax error")
        cmd = "commit"
        child.sendline(cmd)
        ex = child.expect(["Commit OK","Commit failed"])
        if ex == 1:
            raise Exception("commit failed")
        else:
            print("Deleted.")

    @staticmethod
    def add_sfc_gateway(target_switch: str, vrf_id: str, gateway: str):
        child = try_login(target_switch)
        child.sendline("configure")
        child.expect("#")
        cmd = "set protocols static vrf \"%s\" route 0.0.0.0/0 next-hop %s" %(vrf_id, gateway)
        child.sendline(cmd)
        child.expect("#")
        child.sendline("commit")
        child.expect("#")
        ex = child.expect(["Commit OK","Commit failed"])
        if ex == 1:
            raise Exception("commit failed")
        else:
            print("Added.")

    @staticmethod
    def remove_sfc_gateway(target_switch: str, vrf_id: str):
        child = try_login(target_switch)
        child.sendline("configure")
        child.expect("#")
        cmd = "delete protocols static vrf \"%s\" route 0.0.0.0/0" %(vrf_id)
        child.sendline(cmd)
        ex = child.expect(["Deleting", "syntax error"])
        if ex == 1:
            raise Exception("systax error")
        child.sendline("commit")
        child.expect("#")
        ex = child.expect(["Commit OK","Commit failed"])
        if ex == 1:
            raise Exception("commit failed")
        else:
            print("Removed.")


    @staticmethod
    def create_sfc(target_switch: str, vrf_id: str, vlan_id: int, vif_ip: str, prefix: int):
        child = try_login(target_switch)
        child.logfile = sys.stdout
        child.sendline("configure")
        child.expect("#")
        cmd = "set vlans vlan-id %s l3-interface \"vlan%s\"" %(str(vlan_id), str(vlan_id) )
        child.sendline(cmd)
        child.expect("#")
        cmd = "set vlan-interface interface vlan%s vrf \"%s\"" %(str(vlan_id), vrf_id)
        child.sendline(cmd)
        child.expect("#")
        cmd = "set vlan-interface interface vlan%s vif vlan%s address %s prefix-length %s" %(str(vlan_id), str(vlan_id), vif_ip, str(prefix))
        child.sendline(cmd)
        child.expect("#")
        child.sendline("commit")
        child.expect("#")
        ex = child.expect(["Commit OK","Commit failed"])
        if ex == 1:
            raise Exception("commit failed")
        else:
            print("Created.")

    @staticmethod
    def delete_sfc(target_switch: str, vlan_id: int):
        child = try_login(target_switch)
        #child.logfile = sys.stdout
        child.sendline("configure")
        child.expect("#")
        cmd = "delete vlan-interface interface vlan%s" %(str(vlan_id))
        child.sendline(cmd)
        ex = child.expect(["Deleting", "syntax error"])
        if ex == 1:
            raise Exception("systax error")
        cmd = "delete vlans vlan-id %s" %(str(vlan_id))
        child.sendline(cmd)
        ex = child.expect(["Deleting", "syntax error"])
        if ex == 1:
            raise Exception("systax error")
        cmd = "commit"
        child.sendline(cmd)
        ex = child.expect(["Commit OK","Commit failed"])
        if ex == 1:
            raise Exception("commit failed")
        else:
            print("Deleted.")

    @staticmethod
    def get_switch_name(target_switch):
        child = try_login(target_switch)
        child.sendline("show system name\r")
        child.expect("admin@>*")
        child.expect(">")

        return child.before

    @staticmethod
    def create_vrf(target_switch, number):
        child = try_login(target_switch)
        child.sendline("configure")
        child.expect("#")

        step = 0
        for i in range(number):
            child.sendline("set ip vrf test" + str(i))
            child.expect("#")
            child.sendline("commit")
            child.expect("#")
            time.sleep(0.5)
            print ("(%d/%d)" %(i+1, number))
            tmp = int(i / 128)
            if tmp > step:
                past_switch = target_switch
                target_switch = ip2int(past_switch) + 1
                target_switch = int2ip(target_switch)
                step = step + 1
                print ("change swtich from %s to %s" %(past_switch, target_switch))
                child = try_login(target_switch)
                child.sendline("configure")
                child.expect("#")
                
    @staticmethod
    def delete_vrf(target_switch, number):
        child = try_login(target_switch)
        child.sendline("configure")
        child.expect("#")
        step = 0
        for i in range(number):
            child.sendline("delete ip vrf test" + str(i))
            time.sleep(0.5)
            expect = child.expect(["syntax error, expecting", "OK"])
            if expect == 1:
                child.sendline("commit")
                child.expect(["#"])

            print ("(%d/%d)" %(i+1, number))
            tmp = int(i / 128)
            if tmp > step:
                past_switch = target_switch
                target_switch = ip2int(past_switch) + 1
                target_switch = int2ip(target_switch)
                step = step + 1
                print ("change swtich from %s to %s" %(past_switch, target_switch))
                child = try_login(target_switch)
                child.sendline("configure")
                child.expect("#")
        child.sendline("commit")
        child.expect("#")

    @staticmethod
    def show_vrf(target_switch):
        child = try_login(target_switch)
        child.sendline("show vrf | no-more")
        child.expect(".*@*>")
        child.expect("admin@")
        return child.before
        

if __name__ == "__main__":
    print(KulRemote.get_switch_name('10.1.160.222'))
    pass