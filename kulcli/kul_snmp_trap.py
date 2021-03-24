import sys
import threading
import logging

from pysnmp.carrier.asynsock.dispatch import AsynsockDispatcher
from pysnmp.carrier.asynsock.dgram import udp, udp6
from pyasn1.codec.ber import decoder
from pysnmp.proto import api
from pysnmp.smi import builder, view, compiler, rfc1902

logger = logging.getLogger('main.snmptrapd')

class KulSnmpTrapReceiver(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self) 
        mibBuilder = builder.MibBuilder()
        compiler.addMibCompiler(mibBuilder, sources=['/usr/share/snmp/mibs'])
        mibBuilder.loadModules('IF-MIB')
        self.mibView = view.MibViewController(mibBuilder)
        self.transportDispatcher = AsynsockDispatcher()
        self.transportDispatcher.registerRecvCbFun(self.cbFun)
        # UDP/IPv4
        self.transportDispatcher.registerTransport(
            udp.domainName, udp.UdpSocketTransport().openServerMode(('0.0.0.0', 162))
        )
        self.enable = False

    def run(self):
        self.transportDispatcher.jobStarted(1)
        try:
            self.transportDispatcher.runDispatcher()
        except:
            self.transportDispatcher.closeDispatcher()
            self.transportDispatcher.jobFinished(1)

    def stop(self):
        #print ("Exit ... ")
        self.transportDispatcher.closeDispatcher()
        self.transportDispatcher.jobFinished(1)
    
    def snmp_enable(self):
        self.enable = True
    
    def snmp_disable(self):
        self.enable = False

    def cbFun(self, transportDispatcher, transportDomain, transportAddress, wholeMsg):
        while wholeMsg:
            msgVer = int(api.decodeMessageVersion(wholeMsg))
            if msgVer in api.protoModules:
                pMod = api.protoModules[msgVer]
            else:
                #print('Unsupported SNMP version %s' % msgVer)
                return
            reqMsg, wholeMsg = decoder.decode(wholeMsg, asn1Spec=pMod.Message(),)
            if self.enable:
                print('Notification message from %s:%s: ' % (transportDomain, transportAddress))
            reqPDU = pMod.apiMessage.getPDU(reqMsg)
            if reqPDU.isSameTypeWith(pMod.TrapPDU()):
                if msgVer == api.protoVersion1:
                    varBinds = pMod.apiTrapPDU.getVarBindList(reqPDU)
                else:
                    varBinds = pMod.apiTrapPDU.getVarBinds(reqPDU)
                    varBinds = [rfc1902.ObjectType(rfc1902.ObjectIdentity(x[0]), x[1]).resolveWithMib(self.mibView) for x in varBinds]
                    out = ""
                    for varBind in varBinds:
                        out += varBind.prettyPrint() + "\n"
                        if self.enable:
                            print(varBind.prettyPrint()) 
                    logger.info(out)
