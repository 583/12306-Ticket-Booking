# 12306-Ticket-Booking
##基于Python的12306自动订票系统

###系统功能
1.余票监控：发现余票自动下单
2.自动打码：采用第三方免费接口，自动跳过图片验证码
3.小黑屋：发展有余票但是下单失败的车次，自动加入小黑屋
4.邮件通知：下单异常或下单成功后邮件通知用户，以便及时处理
5.全国CDN轮询：提供余票查询频率的同时尽量避免IP被封禁
6.远程日志：抢票日志推送到远程服务器，方便查询
7.动态任务：定时扫描任务变化，动态增减任务
8.并行任务：支持多个抢票任务同时进行
9.远程任务：支持从远程服务器下载任务

###运行环境
Python3.6

###运行截图
<br>运行日志<br>
(img/1.png)
<br>邮件<br>
(img/2.png)
<br>12306订单<br>
(img/3.png)

###使用说明
config/booking.txt--抢票任务配置文件，一行为一个抢票任务，不需要设置的字段留空
utils/sendEmail.py--邮件发送模块，配置发送邮件的账号信息
12306_auto_book.py--主程序
server.py--邮件代发服务端程序
client.py--邮件代发客户端程序(ps: 有些网络下邮件发送失败，需要代发)

###致谢
程序参考了部分开源项目，对以下同仁表示感谢~
下单程序参考 https://github.com/Henryhaohao/12306_Ticket.git 感谢[Henryhaohao](https://github.com/Henryhaohao/12306_Ticket.git) 
全国CDN获取参考 https://github.com/testerSunshine/12306.git 感谢[文贤平](https://github.com/testerSunshine/12306.git)
另外，感谢littlebigluo提供的验证码识别接口：http://littlebigluo.qicp.net:47720/

###总结
订票信息配置正确便可运行，适合有一定编程基础的读者
系统快速开发而成，并应用于2019年春运抢票，请忽略代码质量问题~
希望能帮你抢到一张心仪的票！
欢迎 [提问](https://github.com/itsmartkit/12306-Ticket-Booking/issues) 或来信 itsmartkit@163.com