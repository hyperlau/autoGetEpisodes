#!/usr/bin/env python3

import sys
import os
from autoGetEpisodes import GetConfig
from pmail import Pmail
from pyaria2 import Aria2RPC

if (sys.argv[2]=='0'):
    exit()

# 字节数转换成可读单位
def bytes2human(n):
    symbols = ('KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB')
    prefix = {}
    for i, s in enumerate(symbols):
        prefix[s] = 1 << (i + 1) * 10
    for s in reversed(symbols):
        if n >= prefix[s]:
            value = float(n) / prefix[s]
            return '%.1f%s' % (value,s)
    return '%sB' % n

config=GetConfig().getConfig()

#查询文件
aria2Token=config.get('global','aria2Token')
aria2Url=config.get('global','aria2Url')
downloadDir=os.path.abspath(config.get('global','downloadDir'))
xmlrpc=Aria2RPC(url=aria2Url,token=aria2Token)
xmlrpcReturn=xmlrpc.getFiles(sys.argv[1])

fileCount=sys.argv[2]
title='autoGetEpisodes '+fileCount+'个文件下载完成'
message='以下文件下载完成：\n----------------------\n'

for i in xmlrpcReturn:
    message+='['+i['index']+']:'+i['path']+' | '+'大小:'+bytes2human(int(i['length']))+'\n----------------------\n'

mail=Pmail(config.smtpServerHost,config.smtpServerPort,config.mailFrom,config.smtpPwd)
emailObj = mail.getEmailObj('AutoGetEpisodes '+sys.argv[2]+'个文件下载完成', config.mailFrom, [config.mailTo])
mail.attachContent(emailObj, message)
mail.sendEmail(emailObj, config.mailTo.split(","))


