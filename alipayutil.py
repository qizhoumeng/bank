# -*- coding: utf-8 -*-

'''
支付宝支付
1.AplipayMobile app移动支付，只验证支付成功之后的回调通知
2.AlipayDirect 支付宝及时到账支付，生成请求url，验证支付回调通知
'''

import sys
import requests
import urlparse
import base64

from urllib import urlencode
from hashlib import md5
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA

reload(sys)
sys.setdefaultencoding('utf-8')

INPUT_CHARSET = 'utf-8'


# 手机快捷支付服务器异步通知地址
SECURITY_NOTIFY_URL = ''

# 手机网页支付服务器异步通知地址
WAP_NOTIFY_URL = ''

# 手机网页支付页面同步通知地址
WAP_CALL_BACK_URL = ''


# 支付宝网关
ALIPAY_GATEWAY = 'https://mapi.alipay.com/gateway.do?'

# 支付宝安全验证地址
ALIPAY_VERIFY_URL = 'https://mapi.alipay.com/gateway.do?service=notify_verify&'

# 支付宝合作身份证ID
PARTNER = ''

# 支付宝交易安全检验码，用于MD5加密
KEY = ''

# 支付宝商户私钥，用于RSA加密
PRIVATE_KEY = '''-----BEGIN RSA PRIVATE KEY-----
替换整块
-----END RSA PRIVATE KEY-----'''

# 支付宝公钥，用于RSA验签
ALIPAY_PUBLIC_KEY = '''-----BEGIN PUBLIC KEY-----
替换整块
-----END PUBLIC KEY-----'''

# 字符编码
INPUT_CHARSET = 'utf-8'

# 支付宝账户，所有订单款项都将打到这个账户。必须和支付宝分配的商户ID匹配。
EMAIL = ''


class AplipayException(Exception):

    '''阿里异常'''

    def __init__(self, message):
        self.message = message


class Alipay(object):

    '''支付宝支付'''

    def filter_para(self, paras):
        '''过滤空值和签名'''
        return {
            k: v
            for k, v in paras.items()
            if len(str(v)) and k not in ['sign', 'sign_type']
        }

    def create_linkstring(self, paras):
        '''对参数排序并拼接成query'''
        return u'&'.join([
            u'{k}={v}'.format(k=key, v=paras[key])
            for key in sorted(paras.keys())
        ])

    def _rsa_verify(self, paras):
        '''rsa 验签'''
        sign = base64.b64decode(paras['sign'])
        pub_key = RSA.importKey(ALIPAY_PUBLIC_KEY)
        new_params = self.filter_para(paras)
        content = self.create_linkstring(new_params)
        verifier = PKCS1_v1_5.new(pub_key)
        return verifier.verify(SHA.new(content.encode(INPUT_CHARSET)), sign)

    def _md5_verify(self, paras):
        '''md5验签'''
        sign = paras['sign']
        new_params = self.filter_para(paras)
        paras_str = self.create_linkstring(new_params)
        mysign = self._md5_sign(paras_str)
        return sign == mysign

    def _notify_verify(self, paras):
        '''验证是否是支付宝通知'''
        notify_id = paras['notify_id']
        res = requests.get(
            '{verify_url}notify_id={notify_id}&partner={seller_id}'.format(
                verify_url=ALIPAY_VERIFY_URL,
                notify_id=notify_id, seller_id=PARTNER)
        )
        return res.text == 'true'

    def _md5_sign(self, paras_str):
        '''md5加密'''
        return md5('%s%s' % (paras_str, KEY)).hexdigest()


class AlipayDirect(Alipay):

    '''支付宝即时到账'''

    def __init__(self):
        super(AlipayDirect, self).__init__()

    def build_request_url(self, notify_url, return_url,
                          out_trade_no, subject, total_fee, body, show_url):
        '''生成即时到账请求参数'''
        paras = {
            'partner': PARTNER, 'seller_email': EMAIL,
            '_input_charset': INPUT_CHARSET,
            'service': 'create_direct_pay_by_user',
            'payment_type': '1',  # 商品购买，默认给值
            'notify_url': notify_url, 'return_url': return_url,
            'out_trade_no': out_trade_no, 'subject': subject[:127],
            'total_fee': total_fee, 'body': body[:999],
            'show_url': show_url,
            'anti_phishing_key': '',
            'exter_invoke_ip': '',
            'seller_id': PARTNER
        }
        new_params = self.filter_para(paras)
        paras_str = self.create_linkstring(new_params)
        md5_sign = self._md5_sign(paras_str)
        new_params['sign'] = md5_sign
        new_params['sign_type'] = 'MD5'
        return '%s%s' % (ALIPAY_GATEWAY, urlencode(new_params))

    def real_success(self, paras):
        '''
        1.状态合法性验证
        2. md5验证
        3. 消息有效性验证
        '''
        valid_status = ['TRADE_SUCCESS', 'TRADE_FINISHED']
        if paras['trade_status'] not in valid_status:
            return False, 'trade_status_valid'
        if not self._md5_verify(paras):
            return False, 'md_verify_fail'
        if not self._notify_verify(paras):
            return False, 'notify_verify_fail'
        return True, 'success'


class AplipayMobile(Alipay):

    '''支付宝移动支付'''

    def __init__(self, paras):
        if paras is None:
            raise AplipayException(u'缺少参数')
        super(AplipayMobile, self).__init__()
        self.paras = self.paras_str2dict(
            paras) if type(paras) == str else paras

    def paras_str2dict(self, paras_str):
        '''字符串转换成字典'''
        data = urlparse.parse_qs(paras_str)
        return {key: data[key][0] for key in data.keys()}

    def real_success(self):
        '''
        1.状态合法性验证
        2. rsa验证
        3. 消息有效性验证
        '''
        valid_status = ['TRADE_SUCCESS', 'TRADE_FINISHED']
        if self.paras['trade_status'] not in valid_status:
            return False, 'trade_status_valid'
        if not self._rsa_verify(self.paras):
            return False, 'rsa_verify_fail'
        if not self._notify_verify(self.paras):
            return False, 'notify_verify_fail'
        return True, 'success'


if __name__ == '__main__':
    '''使用🌰'''
    a = AlipayDirect()
    print a.build_request_url(1, 1, 1, 1, 1, 1, 1)
    print a.real_success({'trade_status': 1})

    a = AplipayMobile("discount=0.02BsSGAfVtaBO0Gc7feW%2BNqg8PVo1W0cLOY%3D")
    print a.real_success()
