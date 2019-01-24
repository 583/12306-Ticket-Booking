# -*- coding: utf-8 -*-
"""
Created on Mon Jan  7 18:59:51 2019

@author: cyj
"""
import datetime
import smtplib
from email.mime.text import MIMEText
from email.header import Header

class SendEmail(object):
    def __init__(self):
        self.mail_host = 'smtp.163.com'
        self.mail_user = 'itsmartkit'
        self.mail_pass = ''
        self.sender = 'itsmartkit@163.com'
    def send(self, receivers, subject, content):
        recv_list = receivers.split(',')
        recv_list.append(self.sender)
        send_succ = False
        try:
            message = MIMEText(content, 'html', 'utf-8')
            message['Subject'] = Header(subject, 'utf-8')
            message['From'] = self.sender
            message['To'] =  receivers
            smtpObj = smtplib.SMTP() 
            smtpObj.connect(self.mail_host, 25)    # 25 为 SMTP 端口号
            smtpObj.login(self.mail_user, self.mail_pass)  
            smtpObj.sendmail(self.sender, recv_list, message.as_string())
            println('邮件发送成功！')
            smtpObj.quit()
            send_succ = True
        except smtplib.SMTPException as ex:
            println('Error: 邮件发送失败！')
            print(ex)
        return send_succ
    
def println(msg):
    print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ': ' + msg)
#    cmdTxt = 'log:' + msg
#    client.send(cmdTxt.encode(encoding))
#    thread = threading.Thread(target=socketsend,name='Thread-Socket-Send',args=(cmdTxt,))
#    thread.start()
