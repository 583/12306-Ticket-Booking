# -*- coding: utf-8 -*-
"""
12306-自动抢票
Created on Fri Jan  4 20:49:30 2019

@author: cyj
"""
import base64
import codecs
import datetime
import json
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import pygame
import re
import random
import sys
import ssl
import socket
import schedule
import threading
import time
import requests

from urllib import parse
import urllib3

from utils.cdnUtils import CDNProxy
from utils.httpUtils import HTTPClient
from utils.sendEmail import SendEmail

import logging

logger = logging.getLogger('PABS')
logger.setLevel(logging.DEBUG)
# 建立一个filehandler来把日志记录在文件里，级别为debug以上
fh = logging.FileHandler('log/logging.log')
fh.setLevel(logging.DEBUG)
# 设置日志格式
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

fh.setFormatter(formatter)
# 将相应的handler添加在logger对象中
logger.addHandler(fh)

urllib3.disable_warnings() #不显示警告信息
ssl._create_default_https_context = ssl._create_unverified_context
req = requests.Session()

encoding = 'utf-8'

def conversion_int(str):
    return int(str)

def println(msg):
    print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ': ' + str(msg))
    cmdTxt = 'log:' + str(msg)
    logger.info(msg)
    socketsend(cmdTxt)
    
def log(msg):
    logger.info(msg)
    print(msg)

def getip():
    url = 'http://2019.ip138.com/ic.asp'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
    }
    html = req.get(url, headers=headers, verify=False).content
    ip = re.findall(r'(?<![\.\d])(?:\d{1,3}\.){3}\d{1,3}(?![\.\d])', str(html))
    if ip:
        return ip[0]
    else:
        return ''

class Leftquery(object):
    '''余票查询'''
#    global station_name_res
    def __init__(self):
        self.station_url = 'https://kyfw.12306.cn/otn/resources/js/framework/station_name.js'
        self.headers = {
            'Host': 'kyfw.12306.cn',
            'If-Modified-Since': '0',
            'Pragma': 'no-cache',
            'Referer': 'https://kyfw.12306.cn/otn/leftTicket/init',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest'
        }
        self.station_name_res = None

    def station_name(self, station):
        '''获取车站简拼'''
        if self.station_name_res == None:
#            print('获取车站简拼')
#            print(self.station_url)
            html = None
            try:
               html = requests.get(self.station_url, verify=False).text 
            except:
               html = requests.get('http://39.96.21.111/station_name.js', verify=False).text 
#            print(html)
            self.station_name_res = html.split('@')[1:]
#            time.sleep(60)
        dict = {}
        for i in self.station_name_res:
            key = str(i.split('|')[1])
            value = str(i.split('|')[2])
            dict[key] = value
        return dict[station]

    def query(self, n, from_station, to_station, date, cddt_train_types):
        '''余票查询'''
        fromstation = self.station_name(from_station)
        tostation = self.station_name(to_station)
        self.n = n
        host = '58.216.109.187' # 真实ip
#        if cdn_list:
#            host = cdn_list[random.randint(0, len(cdn_list) - 1)]
        log('[' + threading.current_thread().getName() + ']: 余票查询开始，请求主机 --> [' + host + ']')
        url = 'https://'+ host +'/otn/leftTicket/queryZ?leftTicketDTO.train_date={}&leftTicketDTO.from_station={}&leftTicketDTO.to_station={}&purpose_codes=ADULT'.format(
            date, fromstation, tostation)
#        print(url)
        try:
#            proxie = "{'http': 'http://127.0.0.1:8580'}"
            q_res = requests.get(url, headers=self.headers, timeout=3, verify=False)
#            print(q_res)
            html = q_res.json()
#            print(html)
            result = html['data']['result']
            if result == []:
                println('很抱歉,没有查到符合当前条件的列车!')
#                exit()
            else:
                msg = '[' + threading.current_thread().getName() + '] ' + date + ' ' + from_station + '-' + to_station + ' 第[' + str(self.n) + ']次查询成功!'
                log('\n' + '*' * 6 + msg + '*' * 6 + '\n')
                cmdTxt = 'log:' + msg
                try:
                    client.sendall(cmdTxt.encode(encoding))
                except:
                    pass
                # 打印出所有车次信息
                num = 1  # 用于给车次编号,方便选择要购买的车次
                for i in result:
#                    print(i)
                    info = i.split('|')
                    if info[0] != '' and info[0] != 'null':
#                        print(i)
#                        print(str(num) + '.' + info[3] + '车次还有余票:')
#                        println(info[3] + '车次还有余票:')
                        show_flag = False
                        if len(cddt_train_types) == 0:
                            show_flag = True
                        else:   
                            for t in cddt_train_types:
                                if t == info[3][0:1]:
                                    show_flag = True
                                    break
                        if not show_flag:
                            continue
                        ticketInfo = '【' + info[3] + '车次还有余票】: ' + '出发时间:' + info[8] + ' 到达时间:' + info[9] + ' 历时:' + info[10] + ' '
#                        print(ticketInfo, end='')
                        seat = {21: '高级软卧', 23: '软卧', 26: '无座', 28: '硬卧', 29: '硬座', 30: '二等座', 31: '一等座', 32: '商务座',
                                33: '动卧'}
                        from_station_no = info[16]
                        to_station_no = info[17]
                        for j in seat.keys():
                            if info[j] != '无' and info[j] != '':
                                if info[j] == '有':
                                    ticketInfo = ticketInfo + seat[j] + ':有票 '
#                                    print(seat[j] + ':有票 ', end='')
                                else:
                                    ticketInfo = ticketInfo + seat[j] + ':有' + info[j] + '张票 '
#                                    print(seat[j] + ':有' + info[j] + '张票 ', end='')
                        println(ticketInfo)
#                        print('\n')
#                    elif info[1] == '预订':
#                        print(str(num) + '.' + info[3] + '车次暂时没有余票')
#                    elif info[1] == '列车停运':
#                        print(str(num) + '.' + info[3] + '车次列车停运')
#                    elif info[1] == '23:00-06:00系统维护时间':
#                        print(str(num) + '.' + info[3] + '23:00-06:00系统维护时间')
#                    else:
#                        print(str(num) + '.' + info[3] + '车次列车运行图调整,暂停发售')
                    num += 1
            if host in time_out_cdn:
                time_out_cdn.pop(host)
            return result
        except Exception as e:
            if host != 'kyfw.12306.cn' and str(e).find('timeout') > -1:
                if host in time_out_cdn:
                    time_out_cdn.update({host : int(time_out_cdn[host]) + 1})
                else:
                    time_out_cdn.update({host : 1})
                if int(time_out_cdn[host]) > 2:
                    cdn_list.remove(host)
            println('查询余票信息异常: ' + str(e))
#            print(e)
#            exit()



class Login(object):
    '''登录模块'''

    def __init__(self):
        self.username = username
        self.password = password
        self.url_pic = 'https://kyfw.12306.cn/passport/captcha/captcha-image?login_site=E&module=login&rand=sjrand&0.15905700266966694'
        self.url_check = 'https://kyfw.12306.cn/passport/captcha/captcha-check'
        self.url_login = 'https://kyfw.12306.cn/passport/web/login'
        self.url_captcha = 'http://littlebigluo.qicp.net:47720/'
        self.headers = {
            'Host': 'kyfw.12306.cn',
            'Referer': 'https://kyfw.12306.cn/otn/login/init',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
        }

    def showimg(self):
        '''显示验证码图片'''
        global req
        html_pic = req.get(self.url_pic, headers=self.headers, verify=False).content
        open('pic.jpg', 'wb').write(html_pic)
        img = mpimg.imread('pic.jpg')
        plt.imshow(img)
        plt.axis('off')
        plt.show()

    def captcha(self, answer_num):
        '''填写验证码'''
        answer_sp = answer_num.split(',')
        answer_list = []
        an = {'1': (31, 35), '2': (116, 46), '3': (191, 24), '4': (243, 50), '5': (22, 114), '6': (117, 94),
              '7': (167, 120), '8': (251, 105)}
        for i in answer_sp:
            for j in an.keys():
                if i == j:
                    answer_list.append(an[j][0])
                    answer_list.append(',')
                    answer_list.append(an[j][1])
                    answer_list.append(',')
        s = ''
        for i in answer_list:
            s += str(i)
        answer = s[:-1]
        # 验证验证码
        form_check = {
            'answer': answer,
            'login_site': 'E',
            'rand': 'sjrand'
        }
        global req
        html_check = req.post(self.url_check, data=form_check, headers=self.headers, verify=False).json()
        println(html_check)
        if html_check['result_code'] == '4':
            println('验证码校验成功!')
        else:
            println('验证码校验失败!')
            exit()

    def login(self):
        '''登录账号'''
        form_login = {
            'username': self.username,
            'password': self.password,
            'appid': 'otn'
        }
        global req
        html_login = req.post(self.url_login, data=form_login, headers=self.headers, verify=False).json()
        println(html_login)
        if html_login['result_code'] == 0:
            println('恭喜您, 登录成功!')
        else:
            println('账号、密码或验证码错误, 登录失败!')
            exit()


class Order(object):
    '''提交订单'''

    def __init__(self):
        self.url_uam = 'https://kyfw.12306.cn/passport/web/auth/uamtk'
        self.url_uamclient = 'https://kyfw.12306.cn/otn/uamauthclient'
        self.url_order = 'https://kyfw.12306.cn/otn/leftTicket/submitOrderRequest'
        self.url_token = 'https://kyfw.12306.cn/otn/confirmPassenger/initDc'
        self.url_pass = 'https://kyfw.12306.cn/otn/confirmPassenger/getPassengerDTOs'
        self.url_confirm = 'https://kyfw.12306.cn/otn/confirmPassenger/confirmSingleForQueue'
        self.url_checkorder = 'https://kyfw.12306.cn/otn/confirmPassenger/checkOrderInfo'
        self.url_count = 'https://kyfw.12306.cn/otn/confirmPassenger/getQueueCount'
        self.head_1 = {
            'Host': 'kyfw.12306.cn',
            'Referer': 'https://kyfw.12306.cn/otn/leftTicket/init',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
        }
        self.head_2 = {
            'Host': 'kyfw.12306.cn',
            'Referer': 'https://kyfw.12306.cn/otn/confirmPassenger/initDc',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
        }

    def auth(self):
        '''验证uamtk和uamauthclient'''
        # 验证uamtk
        form = {
            'appid': 'otn',
            # '_json_att':''
        }
        global req
        html_uam = req.post(self.url_uam, data=form, headers=self.head_1, verify=False).json()
        println(html_uam)
        if html_uam['result_code'] == 0:
            println('恭喜您,uam验证成功!')
        else:
            println('uam验证失败!')
            return False
#            exit()
        # 验证uamauthclient
        tk = html_uam['newapptk']

        form = {
            'tk': tk,
            # '_json_att':''
        }
        html_uamclient = req.post(self.url_uamclient, data=form, headers=self.head_1, verify=False).json()
        println(html_uamclient)
        if html_uamclient['result_code'] == 0:
            println('恭喜您,uamclient验证成功!')
        else:
            println('uamclient验证失败!')
            return False
        return True
#            exit()

    def order(self, result, train_number, from_station, to_station, date):
        '''提交订单'''
        # 用户选择要购买的车次的序号
        secretStr = parse.unquote(result[int(train_number) - 1].split('|')[0])
        log(secretStr)
        back_train_date = time.strftime("%Y-%m-%d", time.localtime())
        form = {
            'secretStr': secretStr,  # 'secretStr':就是余票查询中你选的那班车次的result的那一大串余票信息的|前面的字符串再url解码
            'train_date': date,  # 出发日期(2018-04-08)
            'back_train_date': back_train_date,  # 查询日期
            'tour_flag': 'dc',  # 固定的
            'purpose_codes': 'ADULT',  # 成人票
            'query_from_station_name': from_station,  # 出发地
            'query_to_station_name': to_station,  # 目的地
            'undefined': ''  # 固定的
        }
        global req
        html_order = req.post(self.url_order, data=form, headers=self.head_1, verify=False).json()
        log(html_order)
        if html_order['status'] == True:
            println('尝试提交订单...')
        else:
            msg = '提交订单失败! '
            if  'messages' in html_order:
                msg = msg + html_order['messages'][0]
            println(msg)
        return html_order
#            exit()

    def price(self):
        '''打印票价信息'''
        form = {
            '_json_att': ''
        }
        global req
        html_token = req.post(self.url_token, data=form, headers=self.head_1, verify=False).text
        token = re.findall(r"var globalRepeatSubmitToken = '(.*?)';", html_token)[0]
        leftTicket = re.findall(r"'leftTicketStr':'(.*?)',", html_token)[0]
        key_check_isChange = re.findall(r"'key_check_isChange':'(.*?)',", html_token)[0]
        train_no = re.findall(r"'train_no':'(.*?)',", html_token)[0]
        stationTrainCode = re.findall(r"'station_train_code':'(.*?)',", html_token)[0]
        fromStationTelecode = re.findall(r"'from_station_telecode':'(.*?)',", html_token)[0]
        toStationTelecode = re.findall(r"'to_station_telecode':'(.*?)',", html_token)[0]
        date_temp = re.findall(r"'to_station_no':'.*?','train_date':'(.*?)',", html_token)[0]
        timeArray = time.strptime(date_temp, "%Y%m%d")
        timeStamp = int(time.mktime(timeArray))
        time_local = time.localtime(timeStamp)
        train_date_temp = time.strftime("%a %b %d %Y %H:%M:%S", time_local)
        train_date = train_date_temp + ' GMT+0800 (中国标准时间)'
        train_location = re.findall(r"tour_flag':'.*?','train_location':'(.*?)'", html_token)[0]
        purpose_codes = re.findall(r"'purpose_codes':'(.*?)',", html_token)[0]
        
        println('token值:' + token)
        println('leftTicket值:' + leftTicket)
        println('key_check_isChange值:' + key_check_isChange)
        println('train_no值:' + train_no)
        println('stationTrainCode值:' + stationTrainCode)
        println('fromStationTelecode值:' + fromStationTelecode)
        println('toStationTelecode值:' + toStationTelecode)
        println('train_date值:' + train_date)
        println('train_location值:' + train_location)
        println('purpose_codes值:' + purpose_codes)
        
        price_list = re.findall(r"'leftDetails':(.*?),'leftTicketStr", html_token)[0]
        # price = price_list[1:-1].replace('\'', '').split(',')
        println('票价:')
        priceInfo = ''
        for i in eval(price_list):
            # p = i.encode('latin-1').decode('unicode_escape')
            priceInfo = priceInfo + i + ' | '
#            print(i + ' | ', end='')
        println(priceInfo)
        return train_date, train_no, stationTrainCode, fromStationTelecode, toStationTelecode, leftTicket, purpose_codes, train_location, token, key_check_isChange

    def passengers(self, token):
        '''打印乘客信息'''
        # 确认乘客信息
        form = {
            '_json_att': '',
            'REPEAT_SUBMIT_TOKEN': token
        }
        global req
        html_pass = req.post(self.url_pass, data=form, headers=self.head_1, verify=False).json()
        passengers = html_pass['data']['normal_passengers']
#        print('\n')
#        print('乘客信息列表:')
#        for i in passengers:
#            print(str(int(i['index_id']) + 1) + '号:' + i['passenger_name'] + ' ', end='')
#        print('\n')
        return passengers

    def chooseseat(self, passengers, passengers_name, stationTrainCode, choose_seat, token):
        '''选择乘客和座位'''
        seat_dict = {'无座': '1', '硬座': '1', '硬卧': '3', '软卧': '4', '高级软卧': '6', '动卧': 'F', '二等座': 'O', '一等座': 'M',
                     '商务座': '9'}
        choose_type = seat_dict[choose_seat]
        if choose_seat == '无座' and stationTrainCode.find('D') == 0:
            choose_type = 'O'
        pass_num = len(passengers_name.split(','))  # 购买的乘客数
        pass_list = passengers_name.split(',')
        pass_dict = []
        for i in pass_list:
            info = passengers[int(i) - 1]
            pass_name = info['passenger_name']  # 名字
            pass_id = info['passenger_id_no']  # 身份证号
            pass_phone = info['mobile_no']  # 手机号码
            pass_type = info['passenger_type']  # 证件类型
            dict = {
                'choose_type': choose_type,
                'pass_name': pass_name,
                'pass_id': pass_id,
                'pass_phone': pass_phone,
                'pass_type': pass_type
            }
            pass_dict.append(dict)

        num = 0
        TicketStr_list = []
        for i in pass_dict:
            if pass_num == 1:
                TicketStr = i['choose_type'] + ',0,1,' + i['pass_name'] + ',' + i['pass_type'] + ',' + i[
                    'pass_id'] + ',' + i['pass_phone'] + ',N'
                TicketStr_list.append(TicketStr)
            elif num == 0:
                TicketStr = i['choose_type'] + ',0,1,' + i['pass_name'] + ',' + i['pass_type'] + ',' + i[
                    'pass_id'] + ',' + i['pass_phone'] + ','
                TicketStr_list.append(TicketStr)
            elif num == pass_num - 1:
                TicketStr = 'N_' + i['choose_type'] + ',0,1,' + i['pass_name'] + ',' + i['pass_type'] + ',' + i[
                    'pass_id'] + ',' + i['pass_phone'] + ',N'
                TicketStr_list.append(TicketStr)
            else:
                TicketStr = 'N_' + i['choose_type'] + ',0,1,' + i['pass_name'] + ',' + i['pass_type'] + ',' + i[
                    'pass_id'] + ',' + i['pass_phone'] + ','
                TicketStr_list.append(TicketStr)
            num += 1

        passengerTicketStr = ''.join(TicketStr_list)
        log(passengerTicketStr)

        num = 0
        passengrStr_list = []
        for i in pass_dict:
            if pass_num == 1:
                passengerStr = i['pass_name'] + ',' + i['pass_type'] + ',' + i['pass_id'] + ',1_'
                passengrStr_list.append(passengerStr)
            elif num == 0:
                passengerStr = i['pass_name'] + ',' + i['pass_type'] + ',' + i['pass_id'] + ','
                passengrStr_list.append(passengerStr)
            elif num == pass_num - 1:
                passengerStr = '1_' + i['pass_name'] + ',' + i['pass_type'] + ',' + i['pass_id'] + ',1_'
                passengrStr_list.append(passengerStr)
            else:
                passengerStr = '1_' + i['pass_name'] + ',' + i['pass_type'] + ',' + i['pass_id'] + ','
                passengrStr_list.append(passengerStr)
            num += 1

        oldpassengerStr = ''.join(passengrStr_list)
        println(oldpassengerStr)
        form = {
            'cancel_flag': '2',
            'bed_level_order_num': '000000000000000000000000000000',
            'passengerTicketStr': passengerTicketStr,
            'oldPassengerStr': oldpassengerStr,
            'tour_flag': 'dc',
            'randCode': '',
            'whatsSelect': '1',
            '_json_att': '',
            'REPEAT_SUBMIT_TOKEN': token
        }
        global req
        html_checkorder = req.post(self.url_checkorder, data=form, headers=self.head_2, verify=False).json()
        println(html_checkorder)
        if html_checkorder['status'] == True:
            println('检查订单信息成功!')
        else:
            println('检查订单信息失败!')
#            exit()

        return passengerTicketStr, oldpassengerStr, choose_type

    def leftticket(self, train_date, train_no, stationTrainCode, choose_type, fromStationTelecode, toStationTelecode,
                   leftTicket, purpose_codes, train_location, token):
        '''查看余票数量'''
        form = {
            'train_date': train_date,
            'train_no': train_no,
            'stationTrainCode': stationTrainCode,
            'seatType': choose_type,
            'fromStationTelecode': fromStationTelecode,
            'toStationTelecode': toStationTelecode,
            'leftTicket': leftTicket,
            'purpose_codes': purpose_codes,
            'train_location': train_location,
            '_json_att': '',
            'REPEAT_SUBMIT_TOKEN': token
        }
        global req
        html_count = req.post(self.url_count, data=form, headers=self.head_2, verify=False).json()
        println(html_count)
        if html_count['status'] == True:
#            println('查询余票数量成功!')
            ticket = html_count['data']['ticket']
            ticket_split = sum(map(conversion_int, ticket.split(','))) if ticket.find(',') != -1 else ticket
            countT = html_count['data']['countT']
                # if int(countT) is 0:
            println(u'排队成功, 你排在: 第 {1} 位, 该坐席类型还有余票: {0} 张'.format(ticket_split, countT))
#            count = html_count['data']['ticket']
#            println('此座位类型还有余票' + count + '张~')
        else:
            println('检查余票数量失败!')
#            exit()


    def confirm(self, passengerTicketStr, oldpassengerStr, key_check_isChange, leftTicket, purpose_codes,
                train_location, token):
        '''最终确认订单'''
        form = {
            'passengerTicketStr': passengerTicketStr,
            'oldPassengerStr': oldpassengerStr,
            'randCode': '',
            'key_check_isChange': key_check_isChange,
            'choose_seats': '',
            'seatDetailType': '000',
            'leftTicketStr': leftTicket,
            'purpose_codes': purpose_codes,
            'train_location': train_location,
            '_json_att': '',
            'whatsSelect': '1',
            'roomType': '00',
            'dwAll': 'N',
            'REPEAT_SUBMIT_TOKEN': token
        }
        global req
        html_confirm = req.post(self.url_confirm, data=form, headers=self.head_2, verify=False).json()
        println(html_confirm)
        #  {'validateMessagesShowId': '_validatorMessage', 'status': True, 'httpstatus': 200, 'data': {'errMsg': '余票不足！', 'submitStatus': False}
        resDict = {}
        msg = ''
        if html_confirm['status'] == True and html_confirm['data']['submitStatus'] == True:
            resDict.update({'status': True})
#            println('确认购票成功!')
#            return True
            msg = '确认购票成功, 出票中...'
        else:
#            println('确认购票失败: {}'.format(html_confirm['data']['errMsg']))
#            return False
            resDict.update({'status' : False})
            msg = '确认购票失败: {}'.format(html_confirm['data']['errMsg'])
        resDict.update({'msg' : msg})
        println(msg)
        return resDict

class Cancelorder(Login, Order):
    '''取消订单'''

    def __init__(self):
        Login.__init__(self)
        Order.__init__(self)
        self.url_ordeinfo = 'https://kyfw.12306.cn/otn/queryOrder/queryMyOrderNoComplete'
        self.url_cancel = 'https://kyfw.12306.cn/otn/queryOrder/cancelNoCompleteMyOrder'
        self.head_cancel = {
            'Host': 'kyfw.12306.cn',
            'Referer': 'https://kyfw.12306.cn/otn/queryOrder/initNoComplete',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
        }

    def orderinfo(self):
        '''查询未完成订单'''
        form = {
            '_json_att': ''
        }
        global req
        res = {'status': False}
        html_orderinfo = req.post(self.url_ordeinfo, data=form, headers=self.head_cancel, verify=False).json()
        println(html_orderinfo)
        if html_orderinfo['status'] == True:
#            println('查询未完成订单成功!')
            try:
                n = 0
                while True and n < 36:
                    if 'orderCacheDTO' in html_orderinfo['data']:
                        n += 1
                        orderCacheDTO = html_orderinfo['data']['orderCacheDTO']
                        if 'waitTime' in orderCacheDTO:
                            time.sleep(int(orderCacheDTO['waitTime']) * 2)
                            html_orderinfo = req.post(self.url_ordeinfo, data=form, headers=self.head_cancel, verify=False).json()
                            println('第[' + str(n) + ']次查询订单状态...')
                        else:
                            time.sleep(5)
                    if 'orderDBList' in html_orderinfo['data']:
                        break
                if 'orderDBList' in html_orderinfo['data']:  
                    order_info = html_orderinfo['data']['orderDBList'][0]
                    pass_list = order_info['array_passser_name_page']
                    sequence_no = order_info['tickets'][0]['sequence_no']
                    train_date = order_info['start_train_date_page']
                    from_station = order_info['from_station_name_page'][0]
                    to_station = order_info['to_station_name_page'][0]
                    log('订单详情:')
                    oInfo = train_date, from_station, to_station, pass_list, sequence_no
                    println(oInfo)
                    res.update({'status' : True})
                    res.update({'sequence_no' : sequence_no})
                    res.update({'start_train_date_page' : order_info['start_train_date_page']})
                    res.update({'msg' : '获取未完成订单成功！'})
                else:
                    if 'orderCacheDTO' in html_orderinfo['data']:
                        res.update({'status' : True})
                        res.update({'msg' : '下单成功，系统正在为您分配坐席...'})
                    else:             
                        res.update({'status' : False})
                        res.update({'msg' : '您没有未完成的订单！'})              
#                return sequence_no
            except Exception as e:
                res.update({'status' : False})
                res.update({'msg' : '查询未完成订单异常！'})
                println(e)
#                exit()
        else:
            res.update({'msg' : '查询未完成订单失败！'})
        return res
#            exit()

    def confirmcancel(self, sequence_no):
        '''确认取消订单'''
        print('\n')
        i = input('是否确定取消该订单?(Y or N):')
        if i == 'Y' or i == 'y':
            form = {
                'sequence_no': sequence_no,  # 订单号('EF20783324')
                'cancel_flag': 'cancel_order',  # 固定
                '_json_att': ''
            }
            global req
            html_cancel = req.post(self.url_cancel, data=form, headers=self.head_cancel, verify=False).json()
            print(html_cancel)
            if html_cancel['status'] == True:
                print('取消订单成功!')
            else:
                print('取消订单失败!')
        else:
            print('退出取消订单程序...')
#            exit()


def pass_captcha():
    '''自动识别验证码'''
    println('正在识别验证码...')
    global req
    url_pic = 'https://kyfw.12306.cn/passport/captcha/captcha-image?login_site=E&module=login&rand=sjrand&0.15905700266966694'
    url_captcha = 'http://littlebigluo.qicp.net:47720/'
    headers = {
        'Host': 'kyfw.12306.cn',
        'Referer': 'https://kyfw.12306.cn/otn/login/init',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
    }
    html_pic = req.get(url_pic, headers=headers, verify=False).content
    base64_str = base64.b64encode(html_pic).decode()
#    print(base64_str)
    open('pic.jpg', 'wb').write(html_pic)
    files = {
        'file': open('pic.jpg', 'rb')
    }
    headers = {
        'Referer': url_captcha,
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
    }
    try:
        return pass_captcha_360(base64_str)
    except Exception as e:
        log(e)
        try:
            res = requests.post(url_captcha, files=files, headers=headers, verify=False).text
            result = re.search('<B>(.*?)</B>', res).group(1).replace(' ', ',')
            return result
        except:
            println('Sorry!验证码自动识别网址已失效~')
    #        exit()

def pass_captcha_360(img_buf):
    url_get_check = 'http://60.205.200.159/api'
    url_img_vcode = 'http://check.huochepiao.360.cn/img_vcode'
    headers1 = {
        'Content-Type': 'application/json',
        'Referer': 'http://60.205.200.159/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
    }
    headers2 = {
        'Referer': 'https://pc.huochepiao.360.cn/',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
    }
    form1 = {
        'base64': img_buf,
    }
    global req
    json_check = req.post(url_get_check, data=json.dumps(form1), headers=headers1, verify=False).json()
#    print(json_check)
    form2 = {
        '=': '',
        'img_buf': img_buf,
        'type': 'D',
        'logon': 1,
        'check':json_check['check']
    }
    json_pass_res = req.post(url_img_vcode, data=json.dumps(form2), headers=headers2, verify=False).json()
    log(json_pass_res)
    an = {'1': (31, 35), '2': (116, 46), '3': (191, 24), '4': (243, 50), '5': (22, 114), '6': (117, 94),
              '7': (167, 120), '8': (251, 105)}
    pass_res = json_pass_res['res'].split('),(')
#    print(pass_res)
    res = ''
    for group in pass_res:
        point = group.replace('(', '').replace(')', '').split(',')
        min_key = '1'
        min_val = sys.maxsize
        for key in an:
            d = pow(an[key][0] - int(point[0]), 2) + pow(an[key][1] - int(point[1]), 2)
            if d < min_val:
                min_val = d
                min_key = key
        if len(res) > 0:
            res = res + ','
        res = res + min_key
#    print(res)
    if len(res) == 0:
        return None
    return res
                
def order(bkInfo):
    '''订票函数'''
    res = {'status': False}
    # 用户输入购票信息:
#    from_station = input('请输入您要购票的出发地(例:北京):')
#    to_station = input('请输入您要购票的目的地(例:上海):')
#    date = input('请输入您要购票的乘车日期(例:2018-03-06):')
    from_station = bkInfo.from_station
    to_station = bkInfo.to_station
    dates = bkInfo.dates
    # 余票查询
    query = Leftquery()
    # 提交订单
    order = None
    n = 0
    avg_time = -1
    
    while res['status'] != True:
        while True:
            now = datetime.datetime.now()
            if now.hour > 22 or now.hour < 6:
                print('['+ datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') +']: 当前时间处于12306网站维护时段，抢票任务挂起中...')
                time.sleep((60 - now.minute) * 60 - now.second + 5)
            else:
                break
        info_key = bkInfo.uuid + '-' + from_station + '-' + to_station
        if thread_list[info_key] == False:
            cddt_trains.pop(info_key)
            booking_list.pop(info_key)
            println('[' + threading.current_thread().getName() + ']: 抢票任务发生变动，当前线程退出...')
            break
        if booking_list[info_key] == True:
            try_count[info_key] += n
            res['status'] = True
            break
        n += 1
#        st = round(random.uniform(0.2 * len(booking_list), (7 - int(bkInfo.rank)) / 2) + random.uniform(0, len(booking_list) / 2.0), 2)
#        st = 0
        st = round(5 + random.uniform(0, 1), 2)
#        if len(cdn_list) < 3:
#            st = 1
#        st = round(st + random.uniform(0.5, len(booking_list)), 2)
        avg_time = (avg_time == -1) and st or (avg_time + st) / 2
        print('平均[' + str(round(avg_time,2)) + ']秒查询一次,下次查询[' + str(st) + ']秒后...')
        time.sleep(st)
        t_no = ''
        p_name = ''
        for date in dates:
            try:
                # 防止多次多线程并发封禁ip
                lock.acquire()
                str_now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                global last_req_time
                if last_req_time == str_now:
                    time.sleep(round(random.uniform(1, (7 - int(bkInfo.rank)) / 2), 2))
                last_req_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                lock.release()
#                print('[' + threading.current_thread().getName() + '] '+ last_req_time + ': 余票查询开始...')
                result = query.query(n, from_station, to_station, date, bkInfo.cddt_train_types)
                if result == None:
                    n -= 1
                    continue
                # 用户选择要购买的车次的序号
                '''判断候选车次'''
                seat = {21: '高级软卧', 23: '软卧', 26: '无座', 28: '硬卧', 29: '硬座', 30: '二等座', 31: '一等座', 32: '商务座',
                    33: '动卧'}
                cddt_seat_keys = []
                for cddt_seat in bkInfo.candidate_seats:
                    for k in seat.keys():
                        if seat[k] == cddt_seat:
                            cddt_seat_keys.append(k)
                            break
                trains_idx = []   
                temp_trains_idx = []
                num = 1
                for i in result:
                    info = i.split('|')
                    if info[0] != '' and info[0] != 'null':
                        pTxt = ''
                        for train in bkInfo.candidate_trains:
                            seat_flag = False
                            for sk in cddt_seat_keys:
                                if info[sk] != '无' and info[sk] != '':
#                                    print(info[3] + info[sk])
                                    seat_flag = True
                                    break
                            if seat_flag:
                                t_tip  = date + '-' + from_station + '-' + to_station + '-' + info[3]
                                if t_tip in ticket_black_list:
                                    temp = '['+ t_tip +']属于小黑屋成员，小黑屋剩余停留时间：' + str(ticket_black_list[t_tip]) + 's'
                                    if pTxt != temp:
                                        pTxt = temp
                                        println(temp)
                                    
                                else:
                                    if info[3] == train:
                                        trains_idx.append(num)
                                    else:
                                        # 出发时间和到达时间符合要求的也可
                                        if len(bkInfo.min_set_out_time) > 0 and len(bkInfo.max_arrival_time) > 0:
                                            msot = bkInfo.min_set_out_time.split(':')
                                            mart = bkInfo.max_arrival_time.split(':')
                                            sot = info[8].split(':') 
                                            art = info[9].split(':')
                                            tsp = info[10].split(':')
                                            t1 = int(sot[0]) * 60 + int(sot[1])
                                            t2 = int(msot[0]) * 60 + int(msot[1])
                                            t3 = int(art[0]) * 60 + int(art[1])
                                            t4 = int(mart[0]) * 60 + int(mart[1])
                                            ts = int(tsp[0]) * 60 + int(tsp[1])
                                            # 保证在区间内
                                            if t1 >= t2 and t3 <= t4 and (t3-t1) >= ts:
        #                                            print(info[3])
                                                temp_trains_idx.append(num)
                    num += 1
                if temp_trains_idx:
                    trains_idx.extend(temp_trains_idx)
                if len(trains_idx) > 0:
                    
                    lock.acquire()
#                    if booking_now[bkInfo.group] > int(bkInfo.rank):
                    if booking_now[bkInfo.group] != 0:
                        time.sleep(1)
                    else:
                        booking_now[bkInfo.group] = int(bkInfo.rank)
                    lock.release()
                    order = Order()
                    auth_res = order.auth()
                    while auth_res != True:
                        # 填写验证码
                        login = Login()
                        answer_num = pass_captcha()
#                        answer_num = input('请输入验证码(例:1,4):')
                        if answer_num == None:
                            time.sleep(3)
                            continue
#                       print(answer_num)
                        login.captcha(answer_num)
                        login.login()
                        auth_res = order.auth()
                        # 发送邮件提醒
                        subject = '自助订票系统--自动登录通知'
                        success_info = '<div>主机[' + local_ip + ']正在尝试登录12306账号[' + bkInfo.username + ']进行抢票前的准备工作，若未收到后续通知，请于20分钟后检查您12306账号中是否有未完成订单。</div><div style="color: #000000; padding-top: 5px; padding-bottom: 5px; font-weight: bold;"><div>'
                        success_info = success_info + '<div><p>---------------------<br/>From: 12306 PABS<br/>' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '</p><div>'
                        email = SendEmail()
                        send_res = email.send(bkInfo.email, subject, success_info) 
                        if send_res == False:
                            println('正在尝试使用邮件代理发送...')
                            cmdTxt = 'addmailtask:' + bkInfo.email + '|' + subject + '|' + success_info
                            try:
                                client.sendall(cmdTxt.encode(encoding))
                                resp = bytes.decode(client.recv(1024), encoding)
                            except:
                                pass
#                        cancelorder = Cancelorder()
#                        res = cancelorder.orderinfo()
                for train_idx in trains_idx:
                    t_no = result[int(train_idx) - 1].split('|')[3]
                    train_tip = date + '-' + from_station + '-' + to_station + '-' + t_no
                    # 如果在黑名单中，不抢票
                    if train_tip in ticket_black_list:
                        #println('['+ train_tip +']属于小黑屋成员，本次放弃下单，小黑屋剩余停留时间：' + str(ticket_black_list[train_tip]) + 's')
                        continue
                    println('正在抢 ' + date + '：[' + t_no + ']次 ' + from_station + '--->' + to_station)
                    train_number = train_idx
                    # 提交订单
                    o_res = order.order(result, train_number, from_station, to_station, date)
                    if o_res['status'] is not True and 'messages' in o_res:
                        if o_res['messages'][0].find('有未处理的订单') > -1 or o_res['messages'][0].find('未完成订单') > -1 :
                            println('您的账户[' + bkInfo.username + ']中有未完成订单，本次任务结束。')
                            subject = '自助订票系统--任务取消通知'
                            success_info = '<div>主机[' + local_ip + ']通知：您的账户[' + bkInfo.username + ']中有未完成订单，请在12306账号[未完成订单]中处理，本次任务结束。</div><div style="color: #000000; padding-top: 5px; padding-bottom: 5px; font-weight: bold;"><div>当前抢票任务信息如下：</div>'
                            success_info = success_info + '[' + date + '，' + from_station + '-->' + to_station + '，' + t_no + '次列车]</div>'
                            success_info = success_info + '<div><p>---------------------<br/>From: 12306 PABS<br/>' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '</p><div>'
                            email = SendEmail()
                            send_res = email.send(bkInfo.email, subject, success_info)
                            playaudio(r'audio/HeartsDesire.mp3')
                            if send_res == False:
                                println('正在尝试使用邮件代理发送...')
                                cmdTxt = 'addmailtask:' + bkInfo.email + '|' + subject + '|' + success_info
                                try:
                                    client.sendall(cmdTxt.encode(encoding))
                                    resp = bytes.decode(client.recv(1024), encoding)
                                except:
                                    pass
                            booking_list[info_key] = True
                            break
                    # 检查订单
                    content = order.price()  # 打印出票价信息
                    passengers = order.passengers(content[8])  # 打印乘客信息
#                    print('乘客信息打印完毕')
                    # 选择乘客和座位
                    '''乘车人'''
                    passengers_name = ''
                    for id_no in bkInfo.passengers_id_no:
                        p_idx = 1
                        for p in passengers:
                            if id_no == p['passenger_id_no']:
                                passengers_name = passengers_name + str(p_idx) + ','
                                p_name = p_name + p['passenger_name']+'(' + p['passenger_id_no'][0:-4] + 'XXXX)'
                                break
                            else:
                               p_idx += 1
                    passengers_name = passengers_name[:-1]
#                    passengers_name = input('请选择您要购买的乘客编号(例:1,4):')
#                    choose_seat = input('请选择您要购买的座位类型(例:商务座):')
#                    print(passengers_name)
                    seat_dic = {21: '高级软卧', 23: '软卧', 26: '无座', 28: '硬卧', 29: '硬座', 30: '二等座', 31: '一等座', 32: '商务座',
                                33: '动卧'}
                    cddt_seats = []
                    for seat in bkInfo.candidate_seats:
                        for idx in seat_dic:
                            t_num = result[int(train_idx) - 1].split('|')[idx]
                            if seat_dic[idx] == seat and t_num != '无' and t_num != '':
                                cddt_seats.append(seat)
                                break
                    for seat in cddt_seats:
                        choose_seat = seat
#                        print(choose_seat)
                        pass_info = order.chooseseat(passengers, passengers_name, content[2], choose_seat, content[8])
                        # 查看余票数
#                        print('查看余票')
                        order.leftticket(content[0], content[1], content[2], pass_info[2], content[3], content[4], content[5], content[6],
                                         content[7], content[8])
                        # 是否确认购票
                        # order.sure()
                        # 最终确认订单
                        res = order.confirm(pass_info[0], pass_info[1], content[9], content[5], content[6], content[7], content[8])
                        
                        if res['status']:
                            cancelorder = Cancelorder()
                            res = cancelorder.orderinfo()
                            if res['status'] != True:
                                println(res['msg'])
                                res.update({'msg' : '出票失败，余票不足！'})
                        if res['status']:
                            booking_list[info_key] = res['status']
                            subject = '自助订票系统--订票成功通知'
                            success_info = '<div>主机[' + local_ip + ']通知：恭喜您，车票预订成功，请及时支付！</div><div style="color: #000000; padding-top: 5px; padding-bottom: 5px; font-weight: bold;"><div>订单信息如下：</div>'
                            success_info = success_info + p_name + '，' + date + '，' + from_station + '-->' + to_station + '，' + t_no + '次列车，' + choose_seat +'。</div>'
                            success_info = success_info + '<div><p>---------------------<br/>From: 12306 PABS<br/>' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '</p><div>'
                            email = SendEmail()
                            send_res = email.send(bkInfo.email, subject, success_info)
                            playaudio(r'audio/HeartsDesire.mp3')
                            if send_res == False:
                                playaudio(r'audio/Lively.mp3')
                                println('正在尝试使用邮件代理发送...')
                                cmdTxt = 'addmailtask:' + bkInfo.email + '|' + subject + '|' + success_info
                                try:
                                    client.sendall(cmdTxt.encode(encoding))
                                    resp = bytes.decode(client.recv(1024), encoding)
                                except:
                                    pass 

                            break
                        else:
                            if res['msg'].find('余票不足') > -1 or res['msg'].find('排队人数现已超过余票数') > -1:
                                println('小黑屋新增成员：['+ train_tip + ']')
                                ticket_black_list.update({train_tip : ticket_black_list_time })
                    if res['status']:
                        break
                    lock.acquire()
                    booking_now[bkInfo.group] = 0
                    lock.release()
            except Exception as e:
                log('['+ datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') +']: 本次下单异常...')
                log(e)
                println('小黑屋新增成员：['+ train_tip + ']')
                ticket_black_list.update({train_tip : ticket_black_list_time })
                
#                if str(e).find('Expecting value') > -1:
                    
#                raise
        
def run(bkInfo):
#    print('1.购票  2.取消订单  3.退票')
#    print('*' * 69)
#    func = input('请输入您要操作的选项(例:1):')
    global username, password
    username = bkInfo.username
    password = bkInfo.password
    println('当前购票账号：' + username)
    flag = False
    n = 0
    while flag == False and n < 5:
        try:
            order(bkInfo)
            flag = True
        except BaseException as ex:
            log(ex)
            n += 1
            time.sleep(3)
            flag = False
            println('第【'+ str(n) +'】次失败重试中...')
           
class BookingInfo(object):
    def __init__(self, bno, group ,rank, username, password, from_station, to_station, dates, passengers_name, passengers_id_no, candidate_trains, candidate_seats, email, set_out, arrival, cddt_train_types):
        # 账号
        self.uuid = bno + '-' + dates
        
        self.group = group
        
        self.username = username
        # 密码
        self.password = password
        # 出发点
        self.from_station = from_station
        # 目的地
        self.to_station = to_station
        # 乘车日期
        self.dates = dates.split(',')
        # 乘车人姓名
        self.passengers_name = passengers_name.split(',')
        # 乘车人证件号码
        self.passengers_id_no = passengers_id_no.split(',')
        # 候选车次
        self.candidate_trains = candidate_trains.split(',')
        # 候选坐席类别
        self.candidate_seats = candidate_seats.split(',')
        # 邮箱
        self.email = email
        # 线程数
        self.rank = rank
        # 最早出发时间
        self.min_set_out_time = set_out
        # 最晚到达时间
        self.max_arrival_time = arrival
        # 火车类型['G','D','K']
        self.cddt_train_types = cddt_train_types.split(',')

def playaudio(path):
    try:
        pygame.mixer.init()
        println('开始播放音乐：' + path)
        track = pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        time.sleep(12)
        pygame.mixer.music.stop()
    except Exception as e:
        log(e)
        
#    client.send(cmdTxt.encode(encoding))
#    thread = threading.Thread(target=socketsend,name='Thread-Socket-Send',args=(cmdTxt,))
#    thread.start()
def socketsend(data):
    try:
        global client
        client.sendall(data.encode(encoding))
        bytes.decode(client.recv(1024), encoding)
    except Exception as e:
        logger.error(e)
#        print(e)
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            client.connect(('39.96.21.111', 12306))
        except:
            logger.error('尝试重连失败！')
            print('尝试重连失败！')
def keepalive():
    try:  
        time_task()
        socketsend(str(time.time()))
    except:
        pass

def task():
    while True:
        now = datetime.datetime.now()
        if now.hour > 22 or now.hour < 6:
            print('['+ datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') +']: 当前时间处于12306网站维护时段，系统将在06:00以后继续抢票...')
            time.sleep((60 - now.minute) * 60 - now.second + 5)
        else:
            break
    println('扫描抢票任务开始...')
    global local_ip
    local_ip = getip()
    filename='config/booking_core.txt'
    fp = codecs.open(filename,'r', encoding='UTF-8')
    booking = fp.readlines()
    fp.close()
    for info_str in booking:
        if len(info_str) < 10:
            continue
        if info_str.find('#') == 0:
            continue
        info = info_str.split('|')
        bkInfo = BookingInfo(info[0], info[1], info[2], info[3], info[4], info[5], info[6], info[7], info[8], info[9], info[10], info[11], info[12], info[13], info[14] ,info[15])
#        run(bkInfo)
        info_key = bkInfo.uuid + '-' + bkInfo.from_station + '-' + bkInfo.to_station
#        print(bkInfo.uuid)
        flag = False
        for key in booking_list:
#            print(key)
            if key == info_key:
                flag = True
                break
        cddt_tra_flag = False
        for key in cddt_trains:
#            print(key)
            if key == info_key:
                cddt_tra_flag = True
                break
        if cddt_tra_flag:
            # 存在则判断是否有变动
            if cddt_trains[info_key] != info[8]:
                # 停止原线程
                thread_list.update({info_key : False})
        else:
            cddt_trains.update({info_key : info[8]})
        if flag == False:
            println(' 添加抢票任务-->' + info_key)
            booking_list.update({info_key : False})
            
            try_count.update({info_key : 0})
    #        ptint(booking_list)
            i = 0
#            t_num = int(bkInfo.rank)
            t_num = 1
            while i < t_num:
                thread = threading.Thread(target=run,name='Core-Thread-'+str((len(thread_list)) * t_num + i +1),args=(bkInfo,))
                thread.start()
                thread_list.update({info_key : True})
                booking_now.update({bkInfo.group : 0})
                i += 1
                time.sleep(round(1 + random.uniform(0, 1), 2))
    # 移除已经删除的任务线程
    for info_key in thread_list:
        if info_key not in booking_list:
            thread_list.update({info_key : False})

def cdn_req(cdn):
    for i in range(len(cdn) - 1):
        http = HTTPClient(0)
        urls = {
            'req_url': '/otn/login/init',
            'req_type': 'get',
            'Referer': 'https://kyfw.12306.cn/otn/index/init',
            'Host': 'kyfw.12306.cn',
            're_try': 1,
            're_time': 0.1,
            's_time': 0.1,
            'is_logger': False,
            'is_test_cdn': True,
            'is_json': False,
        }
        http._cdn = cdn[i].replace("\n", "")
        start_time = datetime.datetime.now()
        rep = http.send(urls)
        if rep and "message" not in rep and (datetime.datetime.now() - start_time).microseconds / 1000 < 500:
            # 如果有重复的cdn，则放弃加入
            if cdn[i].replace("\n", "") not in cdn_list:
                cdn_list.append(cdn[i].replace("\n", ""))
    for to_cdn in time_out_cdn:
        # 移除超时次数大于n的cdn
        if time_out_cdn[to_cdn] > 3 and to_cdn in cdn_list:
            cdn_list.remove(to_cdn)
            time_out_cdn[to_cdn] = 0
#    println(time_out_cdn)
    println(u"所有cdn解析完成, 目前可用[" + str(len(cdn_list)) + "]个")

def cdn_certification():
    """
    cdn 认证
    :return:
    """
    CDN = CDNProxy()
    all_cdn = CDN.open_cdn_file()
    if all_cdn:
        # print(u"由于12306网站策略调整，cdn功能暂时关闭。")
        println(u"开启cdn查询")
        println(u"本次待筛选cdn总数为{}".format(len(all_cdn)))
        t = threading.Thread(target=cdn_req, args=(all_cdn,))
        t.setDaemon(True)
        # t2 = threading.Thread(target=self.set_cdn, args=())
        t.start()
        # t2.start()
    else:
        raise Exception(u"cdn列表为空，请先加载cdn")
def cdn_upd():
    CDN = CDNProxy()
    t = threading.Thread(target=CDN.update_cdn_list, args=())
    t.setDaemon(True)
    # t2 = threading.Thread(target=self.set_cdn, args=())
    t.start()
            
def time_task():
    lock.acquire()
    for t in ticket_black_list:
#        print(ticket_black_list[t])
        ticket_black_list[t] = ticket_black_list[t] - timespan
        if ticket_black_list[t] < 1:
            println('[{}]离开小黑屋'.format(t))
            ticket_black_list.pop(t)
    lock.release()
global booking_list
global cddt_trains
global thread_list
global try_count
global booking_now
global client
global local_ip
cdn_list = []
time_out_cdn = {}
keep_alive_time = 2 # 保活任务，单位s
timespan = 1
ticket_black_list_time = 120 # 小黑屋时间，单位s
ticket_black_list = {}
last_req_time = None
lock = threading.Lock()

if __name__ == '__main__':
    while True:
        now = datetime.datetime.now()
        if now.hour > 22 or now.hour < 6:
            print('['+ datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') +']: 当前时间处于12306网站维护时段，系统将在06:00以后继续抢票...')
            time.sleep((60 - now.minute) * 60 - now.second + 5)
        else:
            break
    log('*' * 30 + '12306自动抢票开始' + '*' * 30)
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    client.connect(('39.96.21.111', 12306))
#    t = threading.Thread(target=keepalive, args=())
#    t.start()
#    client.connect(('127.0.0.1', 12306))
#    schedule.every(keep_alive_time).seconds.do(keepalive)
    booking_list = {}
    cddt_trains = {}
    thread_list = {}
    try_count = {}
    booking_now = {}
    local_ip = getip()
#    time.sleep(300)
#    cdn_certification()

    task()
    schedule.every(10).minutes.do(task)
#    schedule.every(120).minutes.do(cdn_upd)
    schedule.every(timespan).seconds.do(time_task)
    while True: 
        schedule.run_pending()
        time.sleep(1)
    client.close()
    
    
