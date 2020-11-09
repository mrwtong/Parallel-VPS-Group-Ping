# coding=utf-8
"""
Author Wang Tong
"""

import base64
import os
import time
import signal
import re
from urllib.request import urlopen, Request
from Servers import VServer, TServer, SServer


# handle ctrl_c event
def CtrlCHandler(signum, frame):
    print('Stop Ping')
    for server in frame.f_locals.get('serversList'):
        server.StopPing()


''''''
''''''
# table column width
c1 = 8  # index
c2 = 62  # name
c3 = 9  # testRate
c4 = 8  # loss
c5 = 10  # ave
c6 = 10  # min
c7 = 10  # max
#

if __name__ == '__main__':
    # read urlfile
    urlfile = open("urllist.txt", "r")
    print("Reading urllist.txt")
    urllist=[]
    for line in urlfile.readlines():
        if line.startswith('//') or (line == '\n') or line.startswith('#'):
            continue
        urllist.append(line.rstrip('\n'))
    urlfile.close()
    print("Get {len} urls in urllist.txt".format(len=len(urllist)))


    # read serverfile
    print("Reading serverlist.txt")
    serverStrList=[]
    serverfile = open("serverlist.txt", "r")
    for line in serverfile.readlines():
        if line.startswith('//') or (line == '\n') or line.startswith('#'):
            continue
        serverStrList.append(line.rstrip('\n'))
    serverfile.close()
    print("Get {len} servers in serverlist.txt".format(len=len(serverStrList)))

    serversList = []
    print("Downloading Subscribe......\n")
    # add server from  urlfile
    for url in urllist:
        try:
            reqHeader = {'User-Agent': 'Mozilla/5.0 3578.98 Safari/537.36'}
            urlReq = Request(url, headers=reqHeader)
            subData = urlopen(urlReq).read()
        except:
            print('Error in downloading: '+url+'\n')
            continue
        if subData is None:
            continue
        missing_padding = len(subData) % 4
        subData += b'=' * (4 - missing_padding)
        subServers = base64.urlsafe_b64decode(subData).split(b'\n')
        # n=len(subServers)

        for server in subServers:
            head = server.split(b'://')[0]
            if head == b'vmess':
                text = str(server.split(b'://')[1], encoding="ascii")
                serversList.append(VServer(base64.b64decode(text).decode()))
            elif head == b'trojan':
                text = str(server.split(b'://')[1], encoding="ascii")
                serversList.append(TServer(text))
            elif head == b'ssr':
                text = str(server.split(b'://')[1], encoding="ascii")
                missing_padding = len(text) % 4
                text += '=' * (4 - missing_padding)
                serversList.append(SServer(base64.urlsafe_b64decode(text).decode()))


    # add server from  serversfile
    for serverStr in serverStrList:
        head = serverStr.split('://')[0]
        if head == 'vmess':
            serversList.append(VServer(serverStr.split('://')[1]))
        elif head == 'trojan':
            serversList.append(TServer(serverStr.split('://')[1]))
        elif head == 'ssr':
            serversList.append(SServer(serverStr.split('://')[1]))



    # print("Filter Invalid Servers...")
    # for si in range(len(serversList) - 1, -1, -1):
    #     if re.match(r'((2(5[0-5]|[0-4]\d))|[0-1]?\d{1,2})(\.((2(5[0-5]|[0-4]\d))|[0-1]?\d{1,2})){3}', serversList[si].address) is None:
    #         del serversList[si]

    # ping and show result
    # start ping

    while True:

        print("Start ping {} servers...".format(len(serversList)))
        for server in serversList:
            server.RunPingtest(20)
        # show result
        signal.signal(signal.SIGINT, CtrlCHandler)
        signal.signal(signal.SIGTERM, CtrlCHandler)
        time.sleep(4)

        finishedPrecess = 0
        while finishedPrecess < len(serversList):
            finishedPrecess = 0
            clear = os.system("cls")
            for si in range(len(serversList)):
                # print head
                if si == 0:
                    head = '{index:^{c1}}{name:^{c2}}{testRate:^{c3}}{loss:^{c4}}{aver:^{c5}}{min:^{c6}}{max:^{c7}}'.format(
                        c1=c1, c2=c2, c3=c3, c4=c4, c5=c5, c6=c6, c7=c7,
                        index='Index',
                        name='Server Name',
                        testRate='Process',
                        loss='Loss',
                        aver='Aver',
                        min='Min',
                        max='Max')
                    print(head, end='\n', flush=True)
                print(serversList[si].Result(si + 1, c1, c2, c3, c4, c5, c6, c7), end='\n')
                if serversList[si].CheckFinished():
                    finishedPrecess = finishedPrecess + 1
            time.sleep(5)

        while True:
            word = input("Input Index to show server detail(q to quit, r to retest)：")
            if (word == 'r' or word == 'R'):
                break
            elif (word == 'q' or word == 'Q'):
                os._exit()
            elif re.match(r'^[1-9]\d*$', word) is not None:
                index = int(word)
                if index > len(serversList):
                    word = input("Input out of range:")
                print(serversList[index - 1].Detail(index), flush=True)
            else:
                word = input("Input: int num to show details, q to quit, r to retest")
