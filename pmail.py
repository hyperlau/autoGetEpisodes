#!/usr/bin/env python3
# -*- coding:utf-8 -*-
 
import smtplib
import sys
import os
import re
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email import encoders
 
# Python对SMTP支持有smtplib和email两个模块，email负责构造邮件，smtplib负责发送邮件。
class Pmail(object): 

    def __init__(self,emailHost,hostPort,fromAddr,pwd):
        # smtp 邮件服务器
        self.emailHost =emailHost
        # smtp 邮件服务器端口：SSL 连接
        self.hostPort = hostPort
        # 发件地址
        self.fromAddr = fromAddr
        # 发件地址的授权码，而非密码
        self.pwd=pwd


    # 构造邮件对象，并设置邮件主题、发件人、收件人，最后返回邮件对象
    def getEmailObj(self,emailSubject, emailFrom, toAddrList):
        '''
        :param emailSubject:邮件主题
        :param emailFrom:发件人
        :param toAddrList:收件人列表
        :return :邮件对象 emailObj
        '''
        # 构造 MIMEMultipart 对象做为根容器
        emailObj = MIMEMultipart()
        # 将收件人地址用','连接
        emailTo = (",").join(toAddrList)
        print(emailTo)
        # 邮件主题、发件人、收件人
        emailObj['Subject'] = Header(emailSubject, 'utf-8')
        emailObj['From'] = Header(emailFrom, 'utf-8')
        emailObj['To'] = Header(emailTo, 'utf-8')
        return emailObj
     
     
    # 创建邮件正文，并将其附加到跟容器：邮件正文可以是纯文本，也可以是HTML（为HTML时，需设置content_type值为 'html'）
    def attachContent(self,emailObj, emailContent, contentType='plain', charset='utf-8'):
        '''
        :param email_obj:邮件对象
        :param email_content:邮件正文内容
        :param content_type:邮件内容格式 'plain'、'html'..，默认为纯文本格式 'plain'
        :param charset:编码格式，默认为 utf-8
        :return:
        '''
        # 创建邮件正文对象
        content = MIMEText(emailContent, contentType, charset)
        # 将邮件正文附加到根容器
        emailObj.attach(content)
     
     
    # 添加附件：附件可以为照片，也可以是文档
    def attachPart(self,emailObj, partFilePath, partName):
        '''
        :param emailObj:邮件对象
        :param sourcePath:附件源文件路径
        :param partName:附件名
        :return:
        '''
        # 'octet-stream': binary data   创建附件对象
        part = MIMEBase('application', 'octet-stream')
        # 将附件源文件加载到附件对象
        part.set_payload(open(partFilePath, 'rb').read())
        encoders.encode_base64(part)
        # 给附件添加头文件
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % partName)
        # 将附件附加到根容器
        emailObj.attach(part)
     
     
    # 发送邮件
    def sendEmail(self,emailObj,toAddrList):
        '''
        :param emailObj:邮件对象
        :param toAaddrList:收件地址
        :return:发送成功，返回 True；发送失败，返回 False
        '''
        try:
            '''
            # 普通SMTP服务器 smtpObj = smtplib.SMTP([host[, port[, local_hostname]]] )
            # SSL SMTP smtpObj = smtplib.SMTP_SSL([host[, port[, local_hostname]]] )
            # host: SMTP服务器主机。
            # port: SMTP服务端口号，一般情况下SMTP端口号为25,SSL为465
            # 例如 smtpObj = smtplib.SMTP('smtp.qq.com', 25)
            '''
            # 连接 smtp 邮件服务器
            smtpObj = smtplib.SMTP_SSL(self.emailHost, self.hostPort)
            smtpObj.login(self.fromAddr, self.pwd)
            # 发送邮件：email_obj.as_string()：发送的信息
            smtpObj.sendmail(self.fromAddr, toAddrList, emailObj.as_string())
            # 关闭连接
            smtpObj.quit()
            print("发送成功！")
            return True
        except smtplib.SMTPException as e:
            print("发送失败！",e)
            return False
 
 
if __name__ == "__main__":
    if len(sys.argv)<4:
        print("Usage:",sys.argv[0]," toAddrList(split with ,) content subject [partFilePath]")
       	quit()
    # 收件地址
    toAddrList = sys.argv[1]
    emailContent = sys.argv[2]
    emailSubject = sys.argv[3]
    emailFrom = "msg@mailserver.com"
    # smtp 邮件服务器
    emailHost = "smtp.exmail.qq.com"
    # smtp 邮件服务器端口：SSL 连接
    hostPort = 465
    # 发件地址
    fromAddr = "msg@mailserver.com"
    # 密码
    pwd = "mailPwd"
 
    mail=Pmail(emailHost,hostPort,fromAddr,pwd)
    emailObj = mail.getEmailObj(emailSubject, emailFrom, [toAddrList])
    mail.attachContent(emailObj, emailContent)
    if len(sys.argv)==5:
        partFilePath = sys.argv[4]
        partName = os.path.basename(partFilePath)
        mail.attachPart(emailObj, partFilePath, partName)
    mail.sendEmail(emailObj,toAddrList.split(",")) 

