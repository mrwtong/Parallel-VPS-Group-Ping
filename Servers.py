# coding=utf-8
"""
Author Wang Tong
"""

import os
import base64
import time
import signal
import re
import json
import subprocess
from threading import Thread, Lock
from urllib.parse import unquote


class Server:
    def __init__(self, name, address, port):

        # set name and port
        self.name = name
        self.address = address
        self.port = port
        # initialize server quality properties
        self.__minLatency = -1.0
        self.__maxLatency = -1.0
        self.__aveLatency = -1.0
        self.__lost = -1.0
        self.__testRate = -1.0
        self.__pingStartTime = 0.0
        self.__pingProcess = None
        # check pingProcess data
        self.__checkThread = None
        self.__checkFinished = False
        self.__lock = Lock()

    def __ReadResultToClass(self):
        stdout = self.__pingProcess.stdout
        for line in iter(stdout.readline, b''):
            #print(line)
            if line.find(b'iterations') >= 0:
                self.__lock.acquire()
                self.__testRate = float(re.search(r'test:\s*([\d\.\-]+)%', line.decode()).group(1)) / 100
                self.__lock.release()
                # timeout test
                if time.time() - self.__pingStartTime > 60:
                    self.__pingProcess.send_signal(signal.CTRL_C_EVENT)
                    # print('kill timeout process {:d}\nName:{}\n'.format(self.__pingProcess.pid, self.name))

            elif line.find(b'Lost') >= 0:
                self.__lock.acquire()
                self.__lost = float(re.search(r'\(\s*([\d\.\-]+)%\s*loss\)', line.decode()).group(1)) / 100
                self.__lock.release()
            elif line.find(b'Minimum') >= 0:
                self.__lock.acquire()
                self.__minLatency = float(re.search(r'Minimum\s*=\s*([\d\.\-]+)ms', line.decode()).group(1))
                self.__maxLatency = float(re.search(r'Maximum\s*=\s*([\d\.\-]+)ms', line.decode()).group(1))
                self.__aveLatency = float(re.search(r'Average\s*=\s*([\d\.\-]+)ms', line.decode()).group(1))
                self.__lock.release()
        self.__checkFinished = True
        stdout.close()
        return

    def RunPingtest(self, pingNum=20):

        # set default value
        if self.__checkFinished is True:
            self.__checkFinished = False
            self.__minLatency = -1.0
            self.__maxLatency = -1.0
            self.__aveLatency = -1.0
            self.__lost = -1.0
            self.__testRate = -1.0

        if self.__pingProcess is None:
            self.__lock.acquire()
            self.__pingProcess = subprocess.Popen(["psping64.exe", '-q', '-n', str(pingNum), '-i', '0.01', self.address], shell=False, stdout=subprocess.PIPE,
                                                  stderr=subprocess.STDOUT)
            self.__pingStartTime = time.time()
            self.__lock.release()
        elif type(self.__pingProcess) == subprocess.Popen and self.__pingProcess.poll() is not None:
            self.__lock.acquire()
            self.__pingProcess.terminate()
            self.__pingProcess = subprocess.Popen(["psping64.exe", '-q', '-n', str(pingNum), '-i', '0.1', self.address], shell=False, stdout=subprocess.PIPE,
                                                  stderr=subprocess.STDOUT)
            self.__pingStartTime = time.time()
            self.__lock.release()
        else:
            self.__pingProcess.send_signal(signal.CTRL_C_EVENT)
            return

        # use a thread to read result from __pingProcess
        self.__checkThread = Thread(target=self.__ReadResultToClass, daemon=True)
        self.__checkThread.start()

    def CheckFinished(self):
        self.__lock.acquire()
        finished = self.__checkFinished
        self.__lock.release()
        return finished

    def GetTestRate(self):
        self.__lock.acquire()
        testRate = self.__testRate
        self.__lock.release()
        return testRate

    def MinLatency(self):
        self.__lock.acquire()
        min = self.__minLatency
        self.__lock.release()
        return min

    def MaxLatency(self):
        self.__lock.acquire()
        max = self.__maxLatency
        self.__lock.release()
        return max

    def AveLatency(self):
        self.__lock.acquire()
        ave = self.__aveLatency
        self.__lock.release()
        return ave

    def LossRate(self):
        self.__lock.acquire()
        loss = self.__lost
        self.__lock.release()
        return loss

    def StopPing(self):
        if self.__pingProcess.poll() is None:
            self.__pingProcess.send_signal(signal.CTRL_C_EVENT)
        return

    def Result(self, si, col1, col2, col3, col4, col5, col6, col7):
        row = '{index:^{col1}}{name:<{col2}}{testRate:^{col3}}{loss:^{col4}}{aver:^{col5}}{min:^{col6}}{max:^{col7}}'.format(
            col1=col1, col3=col3, col4=col4, col5=col5, col6=col6, col7=col7,
            index='{:d}'.format(si),
            col2=col2 - len(self.name.encode('GBK')) + len(self.name),
            name='{}'.format(self.name),
            testRate='{:.0%}'.format(self.GetTestRate()),
            loss=('-' if self.LossRate() == -1.0 else '{:.0%}'.format(self.LossRate())),
            aver=('-' if (self.AveLatency() == 0.0 or self.AveLatency() == -1.0) else '{:.0f}ms'.format(self.AveLatency())),
            min=('-' if (self.MinLatency() == 0.0 or self.MinLatency() == -1.0) else '{:.0f}ms'.format(self.MinLatency())),
            max=('-' if (self.MaxLatency() == 0.0 or self.MaxLatency() == -1.0) else '{:.0f}ms'.format(self.MaxLatency())))
        return row

    # kill pingProcess when exit
    def __del__(self):
        if self.__pingProcess is not None:
            self.__pingProcess.kill()


class VServer(Server):
    def __init__(self, vServerStr):
        # V2ray subscribed ServerStr format case：
        # {"v":"2","ps":"name","add":"154.17.12.240","port":46522,"id":"UUID","aid":"0","net":"tcp","type":"none"}

        # default address and port
        address = '127.0.0.1'
        port = '1080'
        name = 'V2Ray'
        serverPairs = json.loads(vServerStr)
        # loop
        for pairName in serverPairs.keys():
            if pairName == 'ps':
                name = serverPairs['ps']
                continue
            elif pairName == 'add':
                address = serverPairs['add']
                continue
            elif pairName == 'port':
                port = str(serverPairs['port'])
                continue
            elif pairName == 'id':
                self.id = serverPairs['id']
                continue
            elif pairName == 'aid':
                self.aid = serverPairs['aid']
                continue
            elif pairName == 'net':
                self.net = serverPairs['net']
                continue
            elif pairName == 'type':
                self.type = serverPairs['type']
                continue
        super(VServer, self).__init__(name, address, port)
        del address
        del port
        del name

    def Detail(self, index):
        detail = 'Index: {index}\nName: {name}\nAddress: {address}\nPort: {port}\nID: {id}\nAlterid: {alterid}\n'.format(
            index='{:d}'.format(index),
            name='{}'.format(self.name),
            address='{}'.format(self.address),
            port='{}'.format(self.port),
            id='{}'.format(self.id),
            alterid='{}'.format(self.aid))
        return detail


class TServer(Server):
    def __init__(self, tServerStr):
        # trojan subscribed ServerStr format case：
        # w813vM@154.17.12.240:443?allowInsecure=1&peer=usdd240.ovod.me#%urlname

        self.password = re.search(r'^(.+)@', tServerStr).group(1)
        address = re.search(r'@(.+):', tServerStr).group(1)
        port = re.search(r':(.+)\?', tServerStr).group(1)
        self.allowInsecure = re.search(r'allowInsecure=(.+)&', tServerStr).group(1)
        self.domain = re.search(r'peer=(.+)#', tServerStr).group(1)
        name = unquote(re.search(r'#(.+)$', tServerStr).group(1))

        super(TServer, self).__init__(name, address, port)
        del address
        del port
        del name

    def Detail(self, index):
        detail = 'Index: {index}\nName: {name}\nDomain: {domain}\nAddress: {address}:{port}\nPassword: {password}\n'.format(
            index='{:d}'.format(index),
            name='{}'.format(self.name),
            domain='{}'.format(self.domain),
            address='{}'.format(self.address),
            port='{}'.format(self.port),
            password='{}'.format(self.password))
        return detail


class SServer(Server):
    def __init__(self, sServerStr):
        # SSR subscribed ServerStr format case：
        # tw10.nurobiz.com:60492:origin:aes-128-cfb:http_simple:andXZmsy/?
        # obfsparam=
        # &protoparam=
        # &remarks=
        # &group=
        # ------------------------------
        # "server": tw10.nurobiz.com
        # "port": 60492,
        # "password": "andXZmsy",
        # "method": "aes-128-cfb",
        # "obfs": "http_simple",
        # "obfs_param": "download.windowsupdate.com",
        # "protocol": "origin",
        # "protocol_param": ""

        frontMatch = re.match(r'^(.+):([^:]+):([^:]*):([^:]+):([^:]*):([^:]+)\/\?', sServerStr)
        backPair = sServerStr.split('/?')[1].split('&')
        if frontMatch is None:
            raise IOError('bad ssr subscribe string')

        address = frontMatch.group(1)
        name = frontMatch.group(1)
        port = frontMatch.group(2)
        self.protocol = frontMatch.group(3)
        self.method = frontMatch.group(4)
        self.protocol_param = '-'
        self.obfs = frontMatch.group(5)
        self.obfs_param = '-'
        self.password = base64.urlsafe_b64decode(frontMatch.group(6)).decode(encoding="utf-8")
        self.remark = '-'
        self.group = '-'

        for pair in backPair:
            if re.search(r'^obfsparam=(.+)', pair) is not None:
                text = re.search(r'^obfsparam=(.+)', pair).group(1)
                missing_padding = len(text) % 4
                text += '=' * (4 - missing_padding)
                self.protocol_param = base64.urlsafe_b64decode(text).decode(encoding="utf-8")
                continue
            elif re.search(r'^protoparam=(.+)', pair) is not None:
                text = re.search(r'^protoparam=(.+)', pair).group(1)
                missing_padding = len(text) % 4
                text += '=' * (4 - missing_padding)
                self.protocol_param = base64.urlsafe_b64decode(text).decode(encoding="utf-8")
                continue
            elif re.search(r'^remarks=(.+)', pair) is not None:
                text = re.search(r'^remarks=(.+)', pair).group(1)
                missing_padding = len(text) % 4
                text += '=' * (4 - missing_padding)
                self.remark = base64.urlsafe_b64decode(text).decode(encoding="utf-8")
                self.remark = self.remark.replace('\u0301', '')
                self.remark = self.remark.replace('\uc804', '')
                self.remark = self.remark.replace('\ub77c', '')
                self.remark = self.remark.replace('\ubd81', '')
                self.remark = self.remark.replace('\ub3c4', '')
                self.remark = self.remark.replace('\uc8fc', '')
                self.remark = self.remark.replace('\uc2dc', '')
                name = self.remark
                continue
            elif re.search(r'^gruop=(.+)', pair) is not None:
                text = re.search(r'^gruop=(.+)', pair).group(1)
                missing_padding = len(text) % 4
                text += '=' * (4 - missing_padding)
                self.group = base64.urlsafe_b64decode(text).decode(encoding="utf-8")
                continue

        super(SServer, self).__init__(name, address, port)
        del address
        del port
        del name

    def Detail(self, index):
        detail = 'Index: {index}\nName: {name}\nAddress: {address}:{port}\nPassword: {password}\nMethod: {method}\nProtocol: {protocol}\nProtocolParam: {protocolParam}\nObfs: {obfs}\nObfsParam: {obfsParam}\n'.format(
            index='{:d}'.format(index),
            name='{}'.format(self.name),
            address='{}'.format(self.address),
            port='{}'.format(self.port),
            password='{}'.format(self.password),
            method='{}'.format(self.method),
            protocol='{}'.format(self.protocol),
            protocolParam='{}'.format(self.protocol_param),
            obfs='{}'.format(self.obfs),
            obfsParam='{}'.format(self.obfs_param)
        )

        return detail
