import pexpect
import sys
import time
import socket
import struct


def ip2int(addr):
    return struct.unpack("!I", socket.inet_aton(addr))[0]


def int2ip(addr):
    return socket.inet_ntoa(struct.pack("!I", addr))

class KulRemote:
    def __init__(self):
        pass

    @staticmethod
    def direct_cmd():
        pass

    @staticmethod
    def create_vrf(target_swtich, number):

        child = pexpect.spawn('ssh admin@' + target_swtich, encoding='utf-8')
        #child.logfile = sys.stdout
        child.expect("password:")
        child.sendline("kulpass@123")
        child.expect(">")
        child.sendline("configure")
        child.expect("#")

        step = 0
        for i in range(number):
            child.sendline("set ip vrf test" + str(i))
            child.expect("#")
            child.sendline("commit")
            child.expect("#")
            print ("(%d/%d)" %(i, number-1))
            tmp = int(i / 128)
            if tmp > step:
                past_switch = target_swtich
                new_switch = ip2int(past_switch) + 1
                new_switch = int2ip(new_switch)
                step = step + 1
                print ("change swtich from %s to %s" %(past_switch, new_switch))
                child = pexpect.spawn('ssh admin@' + new_switch, encoding='utf-8')
                child.expect("password:")
                child.sendline("kulpass@123")
                child.expect(">")
                child.sendline("configure")
                child.expect("#")
                
        

    @staticmethod
    def delete_vrf(target_swtich, number):
        child = pexpect.spawn('ssh admin@' + target_swtich, encoding='utf-8')
        
        child.expect("password:")
        child.sendline("kulpass@123")
        child.expect(">")
        child.sendline("configure")
        child.expect("#")
        step = 0
        for i in range(number):
            child.sendline("delete ip vrf test" + str(i))
            time.sleep(0.2)
            expect = child.expect(["syntax error, expecting", "OK"])
            if expect == 1:
                child.sendline("commit")
                child.expect(["#"])

            print ("(%d/%d)" %(i, number-1))
            tmp = int(i / 128)
            if tmp > step:
                past_switch = target_swtich
                new_switch = ip2int(past_switch) + 1
                new_switch = int2ip(new_switch)
                step = step + 1
                print ("change swtich from %s to %s" %(past_switch, new_switch))
                child = pexpect.spawn('ssh admin@' + new_switch, encoding='utf-8')
                child.expect("password:")
                child.sendline("kulpass@123")
                child.expect(">")
                child.sendline("configure")
                child.expect("#")
        child.sendline("commit")
        child.expect("#")

    @staticmethod
    def show_vrf(target_swtich):
        child = pexpect.spawn('ssh admin@' + target_swtich, encoding='utf-8')
        
        child.expect("password:")
        child.sendline("kulpass@123")
        child.expect(">")
        child.sendline("show vrf | no-more")
        child.expect("admin@>*")
        child.expect("admin@>*")
        return child.before
        

if __name__ == "__main__":
    #KulRemote.delete_vrf('10.1.160.222', 128)
    #KulRemote.create_vrf('10.1.160.222', 129)
    #KulRemote.show_vrf('10.1.160.222')

    print(ip2int('10.1.160.222'))
    print(int2ip(ip2int('10.1.160.222')+1))