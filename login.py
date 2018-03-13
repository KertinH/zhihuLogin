# -*- coding: utf-8 -*-
import scrapy
import time
import json
import hmac
from hashlib import sha1
from PIL import Image
from ..settings import zhihu_username,zhihu_password


class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['https://www.zhihu.com/']
    start_urls = ['https://www.zhihu.com']

    headers = {
        # 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.108 Safari/537.36',
        'authorization':'oauth c3cef7c66a1843f8b3a9e6a1e3160e20'
    }



#####################################模拟登录#####################################
    def captcha_judge(self,judge):
        '''判断是否需要验证码，不需要则返回""
           需要则弹出验证码图片，手动输入'''
        if judge is False:
            return ''
        else:
            try:
                captcha = Image.open('captcha.gif')
                captcha.show()
                captcha.close()
                a = input('请输入验证码\n>>')
                return str(a)
            except:
                print('验证码获取失败')


    def get_signature(self,grant_type,client_id,source,timestamp):
        '''生成签名'''
        signature = hmac.new(b'd1b964811afb40118a12068ff74a12f4', None, sha1)
        signature.update(str.encode(grant_type))
        signature.update(str.encode(client_id))
        signature.update(str.encode(source))
        signature.update(str.encode(timestamp))
        return str(signature.hexdigest())


    def start_requests(self):
        '''请求验证码链接'''
        yield scrapy.Request('https://www.zhihu.com/api/v3/oauth/captcha?lang=en',headers=self.headers,
                             callback=self.need_captcha,dont_filter=True)


    def need_captcha(self,response):
        '''根据时间戳获取实时验证码'''
        yield scrapy.Request('https://www.zhihu.com/captcha.gif?r=%d&type=login' % (time.time()*1000),headers=self.headers,callback=self.captcha,
                             meta={'res':response},dont_filter=True)


    def captcha(self,response):
        '''保存验证码并进行登录操作'''
        with open('captcha.gif','wb') as f:
            f.write(response.body)
            f.close()

        judge = json.loads(response.meta.get('res','').text)['show_captcha']
        grant_type = 'password'
        client_id = 'c3cef7c66a1843f8b3a9e6a1e3160e20'
        source = 'com.zhihu.web'
        timestamp = str(int(round(time.time()*1000)))

        form_data = {
            "client_id": client_id,
            "username": zhihu_username,
            "password": zhihu_password,
            "grant_type": grant_type,
            "source": source,
            "timestamp": timestamp,
            "signature": self.get_signature(grant_type,client_id,source,timestamp),#生成签名
            "lang": "cn",
            "ref_source": "homepage",
            "captcha": self.captcha_judge(judge),#获取验证码
            "utm_source": ""
        }

        return scrapy.FormRequest('https://www.zhihu.com/api/v3/oauth/sign_in',formdata=form_data,headers=self.headers,
                                  callback=self.get_cookie,dont_filter=True)


    def get_cookie(self, response):
        '''获取cookie
            进入测试登录链接'''
        yield scrapy.Request('https://www.zhihu.com/inbox',headers=self.headers,callback=self.test_link,dont_filter=True)


    def test_link(self,response):
        '''判断登录是否成功
           成功则进入下一步'''
        if response.status >= 200 and response.status <= 300:
            yield scrapy.Request('https://www.zhihu.com',
                                 headers=self.headers,callback=self.follow_topic,dont_filter=True)
        else:
            print(response.status)
            pass

##############################################################################


    def follow_topic(self,response):
    #这段可以去掉
        with open('zhihu.html', 'wb') as f:
            f.write(response.body)
            f.close()
        pass
