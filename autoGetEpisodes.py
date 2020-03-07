#!/usr/bin/env python3

# -*-coding:utf-8-*-


import time
import getopt
import os
import sys
import re
import logging
import configparser
import requests
from requests.adapters import HTTPAdapter
from bs4 import BeautifulSoup
from pyaria2 import Aria2RPC
from pmail import Pmail

# 读配置文件
class GetConfig(object):
    def __init__(self):
        self.configFile=os.path.abspath('/usr/local/autoGetEpisodes/config.cfg')
       
    def getConfig(self):
        # 读取配置文件
        print('Load Config...')
        config=configparser.ConfigParser()
        config.read(self.configFile, encoding='utf-8')
        # 邮件通知
        config.mailNotify=config.getboolean('global','mailNotify')
        if config.mailNotify:
            config.smtpServerHost=config.get('global','smtpServerHost')
            config.smtpServerPort=config.get('global','smtpServerPort')
            config.smtpPwd=config.get('global','smtpPwd')
            config.mailFrom=config.get('global','mailFrom')
            config.mailTo=config.get('global','mailTo')
            config.mailSub=config.get('global','mailSub')

        # 找出配置文件里的剧集配置
        config.episodesList=[]
        episodesConfigSections=config.sections()
        config.episodesList=[i for i in episodesConfigSections if i !='global'];
        return(config)


# 初始化日志
class logInit(object):
    def __init__(self,config):
        logging.basicConfig(
            level=eval('logging.'+config.get('global','logLevel')),
            format="%(asctime)s---%(lineno)s----%(name)s: %(message)s",
            filename=os.path.abspath(config.get('global','logFile')),
            filemode="a"
        )



# 根据配置文件来抓取url，写入缓存文件
class prepareCacheFile(object):
    def __init__(self,config):
        self.config=config
        self.baseUrl=self.config.get('global','baseUrl')
        self.searchUrl=self.config.get('global','searchUrl')
        self.cacheDir=os.path.abspath(self.config.get('global','cacheDir'))
        self.requestTimeout=self.config.getint('global','requestTimeout')
        self.requestSleep=self.config.getint('global','requestSleep')
        # 创建cache目录
        cacheDirPath=os.path.abspath(self.cacheDir)
        if not os.path.exists(cacheDirPath):
            os.mkdir(cacheDirPath) 
            logging.debug('创建缓存目录 '+cacheDirPath+' 成功!')
        else:
            logging.debug('找到缓存目录'+cacheDirPath)
                # 根据剧集列表创建缓存文件，后面直接读取，不再做判断     
        for i in self.config.episodesList:
            episodeCacheFile=self.getCacheFileAbsPath(i)
            if not os.path.exists(episodeCacheFile):
                with open(episodeCacheFile,'w') as f:
                    logging.debug("创建缓存文件 "+f.name+' 成功!')
            else:
                logging.debug('找到缓存文件'+episodeCacheFile)

    # 返回缓存文件绝对路径
    def getCacheFileAbsPath(self,episodeName):
        return(self.cacheDir+'/'+episodeName+'.cache')

 
    # 获取搜索结果,然后筛选所有符合keyword_1要求的magnetUrl
    def getEpisodesUrls(self,searchUrl,episodesName,keyWord_1):
        head={}
        head['User-Agent']='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.5 Safari/605.1.15'
        # 访问搜索URL得到剧集URL列表
        s=requests.Session()
        s.mount('http://', HTTPAdapter(max_retries=3))
        s.mount('https://', HTTPAdapter(max_retries=3))
        try:
            time.sleep(self.requestSleep)
            req=s.get(searchUrl,headers=head,timeout=self.requestTimeout)
            # 错误就抛出异常
            req.raise_for_status()
        except IOError as e:
            logging.error('一级抓取错误：',e)
            exit(1)
        html=req.text
        bf=BeautifulSoup(html,'html.parser')
        texts=bf.find_all('a',class_='detail-url')
        # 进入剧集页面抓取magnet链接
        results=[]
        for i in texts:
            episodePage=self.baseUrl+'/'+i['href']
            try:
                time.sleep(self.requestSleep)
                reqEpisodesPage=requests.get(episodePage,headers=head,timeout=self.requestTimeout)
                # 错误就抛出异常
                reqEpisodesPage.raise_for_status()
            except IOError as e:
                logging.error('二级抓取错误：',e)
                exit(1)
            epHtml=reqEpisodesPage.text
            epBf=BeautifulSoup(epHtml,'html.parser')
            epTexts=epBf.find('a',class_='mag-url')
            # 根据keyword_1筛选链接
            if re.search(keyWord_1,i.span.string):
                results.append({
                    'magUrl':epTexts['href'],
                    'fileName':i.span.string
                })
        return(results)
    
    # 遍历剧集列表，抓取剧集magnetURL和文件名,写入缓存文件
    def writeCacheFile(self):
        for i in self.config.episodesList:
            cacheFile=self.getCacheFileAbsPath(i)
            keyword_0=self.config.get(i,'keyWord_0')
            keyword_1=self.config.get(i,'keyWord_1')
            # 抓取剧集magnetURL和文件名
            searchURL=self.searchUrl+keyword_0
            logging.info('开始抓取 '+i)
            logging.info('--searchURL='+searchURL)
            logging.info('--筛选关键词：'+keyword_1)
            episodeInfo=self.getEpisodesUrls(searchURL,i,keyword_1)
            epiCache=configparser.ConfigParser()
            # 写入缓存文件
            # 前面初始化的时候已经创建了缓存文件，所以直接read
            cacheFileName=self.getCacheFileAbsPath(i)
            epiCache.read(cacheFileName, encoding='utf-8')
            for j in episodeInfo:
                logging.debug(j)
                # 跳过存在的配置
                if epiCache.has_section(j['fileName']):
                    logging.info('['+j['fileName']+'] 已经存在，skip...')
                    continue
                epiCache[j['fileName']]={
                        'magnetURL':j['magUrl'],
                        'skip':'no'
                        }
                logging.info('['+j['fileName']+'] 写入：')
                logging.info('magnetURL='+j['magUrl'])
                logging.info('skip=no')
            
            with open(cacheFileName,'w') as cacheFile:
                epiCache.write(cacheFile)


# 使用Aria2下载剧集
class GetEpisodes(object):

    def __init__(self,config):
        self.config=config
        # 初始化 aria2 rpc
        logging.info('初始化 aria2 rpc')
        self.aria2Token=self.config.get('global','aria2Token')
        self.aria2Url=self.config.get('global','aria2Url')
        self.downloadDir=os.path.abspath(self.config.get('global','downloadDir'))
        self.jsonrpc=Aria2RPC(url=self.aria2Url,token=self.aria2Token)
        self.jsonrpcOptions = {
            'dir': self.downloadDir
        }

    def download(self,name,url):
        self.jsonrpcOptions['out']=name
        jsonrpcReturn = self.jsonrpc.addUri(
            [url],
            options=self.jsonrpcOptions
        )
        return(jsonrpcReturn)

    def readCacheFile(self):
        self.downloadList=[]
        for i in self.config.episodesList:
            cacheFilePath=os.path.abspath(self.config.get('global','cacheDir')+'/'+i+'.cache')
            logging.debug('读取缓存文件'+cacheFilePath)
            cacheFile=configparser.ConfigParser()
            cacheFile.read(cacheFilePath, encoding='utf-8')
            for s in cacheFile.sections():
                # 跳过skip的文件
                if cacheFile.getboolean(s,'skip') != True:
                    magUrl=cacheFile.get(s,'magneturl')
                    self.downloadList.append({
                        'fileName':s,
                        'magUrl':magUrl
                        })
                    logging.debug('添加到下载列表：\nFileName：'+s+'\nmagUrl:'+magUrl)
                    # 修改skip为True
                    cacheFile.set(s,'skip','yes')
            with open(cacheFilePath,'w') as f:
                cacheFile.write(f)


        logging.debug('下载列表共包含如下 ' + str(len(self.downloadList))+' 条记录：')
        for j in self.downloadList:
            logging.debug(j)


    def downloadFiles(self):
        self.readCacheFile()
        mailContent='共'+str(len(self.downloadList))+'个文件被添加到下载队列:\n'
        for j,i in enumerate(self.downloadList):
            logging.info('添加下载任务：'+i['fileName']+'\nmagnetURL:'+i['magUrl'])
            aria2DownloadID=self.download(i['fileName'],i['magUrl'])
            logging.info('Aria2任务ID：'+aria2DownloadID)
            if self.config.mailNotify:
                mailContent+=str(j+1)+". "+i['fileName']+"\n"
        if self.config.mailNotify:
            mail=Pmail(config.smtpServerHost,config.smtpServerPort,config.mailFrom,config.smtpPwd)
            emailObj = mail.getEmailObj(config.mailSub, config.mailFrom, [config.mailTo])
            mail.attachContent(emailObj, mailContent)
            mail.sendEmail(emailObj, config.mailTo.split(","))



if __name__=='__main__':
    if len(sys.argv)<2:
        print('usage:')
        print(sys.argv[0]+' -g     just only generate cache file')
        print(sys.argv[0]+' -c     generate cache file and get episodes')
        sys.exit(2)
    if sys.argv[1] == '-g':
        config=GetConfig().getConfig()
        logInit(config)
        print('Please Run " tail -f '+os.path.abspath(config.get('global','logFile'))+' " to view the log...')
        logging.info('===开始准备缓存文件===')
        print('===开始准备缓存文件===')
        prepareCacheFile(config).writeCacheFile()
        logging.info('===缓存文件准备完成===')
        print('===缓存文件准备完成===')
        
    elif sys.argv[1] == '-c':
        config=GetConfig().getConfig()
        logInit(config)
        print('Please Run " tail -f '+os.path.abspath(config.get('global','logFile'))+' " to view the log...')
        logging.info('===开始准备缓存文件===')
        print('===开始准备缓存文件===')
        prepareCacheFile(config).writeCacheFile()
        logging.info('===缓存文件准备完成===')
        print('===缓存文件准备完成===')
        print('===添加下载任务===')
        g=GetEpisodes(config)
        g.downloadFiles()
        print('===添加下载任务完成===')


    else:
        print('usage:')
        print(sys.argv[0]+' -g     just only generate cache file')
        print(sys.argv[0]+' -c     generate cache file and get episodes')
        sys.exit(2)
 
