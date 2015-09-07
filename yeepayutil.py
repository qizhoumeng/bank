# -*- coding: utf-8 -*-

'''
易宝支付
1.MERID、KEY 为官方测试帐号，需要更换成分配的商户编号以及秘钥
2.YeepayEBank 为发起支付请求时需要调用的方法，请求时只要请求返回的url 然后把其他参数按照返回的样子，参数名严格区分大小写
3.YeepayEBankNotify 为支付成功后 后台回调通知，这里的url地址需要去官网设置，
4.如果测试的时候，把p8_Url改成本地映射到外网的地址即可，
'''

import sys
import hmac
import urllib


reload(sys)
sys.setdefaultencoding('utf-8')


# 商户编号
MERID = 10001126856

# 商户秘钥
KEY = '69cl522AV6q613Ii4W6u8K6XuW8vM1N6bFgyv769220IuYe9u37N4y7rI4Pl'

# 网银支付请求地址
YeepayEBank_PAY_URL = 'https://www.yeepay.com/app-merchant-proxy/node'


class YeepayException(Exception):

    '''易宝异常'''

    def __init__(self, message):
        self.message = message


class YeepayEBank(object):

    '''易宝网银支付'''

    def __init__(self, p2_order, p3_amt, p5_pid, p6_pcat,
                 p7_pdesc, p8_url, pa_mp):
        '''
        @param p0_cmd 业务类型 固定值:Buy
        @param p1_merid 商户编号
        @param p2_order 商户订单号
        @param p3_amt 支付金额
        @param p4_cur 交易币种 固定值：CNY
        @param p5_pid 商品名称
        @param p6_pcat 商品种类
        @param p7_pdesc 商品描述
        @param p8_url 回调地址 页面跳转地址，后台通知从易宝支付的后台设置
        @param p9_saf 易宝保存送货地址 默认0不需要保存
        @param pa_mp 商户扩展信息
        @param pr_need_response 应答机制 固定值：1 需要应答机制
        @param pd_frp_id 支付通道编码，默认不填写，跳转易宝支付网关
        '''
        self.p0_cmd = 'Buy'
        self.p1_merid = MERID
        self.p2_order = p2_order
        self.p3_amt = p3_amt
        self.p4_cur = 'CNY'
        self.p5_pid = p5_pid[:20]
        self.p6_pcat = p6_pcat[:20]
        self.p7_pdesc = p7_pdesc[:20]
        self.p8_url = p8_url
        self.p9_saf = '0'
        self.pa_mp = pa_mp
        self.pd_frp_id = ''
        self.pr_need_response = '1'

    def create_hmac(self):
        '''
        生成hmac md5
        keys的顺序很重要
        '''
        keys = [
            'p0_cmd', 'p1_merid', 'p2_order', 'p3_amt',
            'p4_cur', 'p5_pid', 'p6_pcat', 'p7_pdesc', 'p8_url',
            'p9_saf', 'pa_mp', 'pd_frp_id', 'pr_need_response'
        ]
        str_old_params = ''.join([str(self.__dict__[key]) for key in keys])
        digest_maker = hmac.new(KEY)
        digest_maker.update(str_old_params)
        return digest_maker.hexdigest()

    def build_pay_params(self):
        hmac = self.create_hmac()
        return {
            'pay_url': YeepayEBank_PAY_URL,
            'p0_Cmd': self.p0_cmd, 'p1_MerId': self.p1_merid,
            'p2_Order': self.p2_order, 'p3_Amt': self.p3_amt,
            'p4_Cur': self.p4_cur, 'p5_Pid': self.p5_pid,
            'p6_Pcat': self.p6_pcat, 'p7_Pdesc': self.p7_pdesc,
            'p8_Url': self.p8_url, 'p9_SAF': self.p9_saf,
            'pa_MP': self.pa_mp, 'pa_FrpId': self.pd_frp_id,
            'pr_NeedResponse': self.pr_need_response,
            'hmac': hmac
        }


class YeepayEBankNotify(object):

    '''易宝网银支付 后台回调通知'''

    def __init__(self, paras):
        self.paras_dict = dict(
            [
                (
                    x.split('=')[0],
                    urllib.unquote_plus(x.split('=')[1]).decode('gbk')
                )
                for x in paras.split('&')
            ]
        )

    def real_success(self):
        '''
        校验加密
        keys的顺序很重要
        '''
        keys = (
            'p1_MerId', 'r0_Cmd', 'r1_Code', 'r2_TrxId', 'r3_Amt', 'r4_Cur',
            'r5_Pid', 'r6_Order', 'r7_Uid', 'r8_MP', 'r9_BType'
        )
        str_old_params = ''.join([self.paras_dict[key] for key in keys])
        digest_maker = hmac.new(KEY)
        digest_maker.update(str_old_params)
        actual_hmac = digest_maker.hexdigest()
        return actual_hmac == self.paras_dict['hmac']


if __name__ == '__main__':
    pass
    # yeepay_ebank = YeepayEBank(
    #     p2_order='', p3_amt=0.01, p5_pid=u'奥特曼', p6_pcat=u'奥特曼种类',
    #     p7_pdesc=u'奥特曼变身蛋', p8_url='http://localhost:8080/Callback.aspx',
    #     pa_mp='测试返回'
    # )
    # print yeepay_ebank.build_pay_params()
    # yeepay_notify = YeepayEBankNotify(
    #     "p1_MerId=10001126856&r0_Cmd=Buy&r1_Code=1&r2_TrxId=868600622222182J&r3_Amt=0.01&r4_Cur=RMB&r5_Pid=%B0%C2%CC%D8%C2%FC%B5%B0&r6_Order=yeepay_84045678&r7_Uid=&r8_MP=%D5%E2%C0%EF%CA%C7%C0%A9%D5%B9+%D0%C5%CF%A2&r9_BType=2&ru_Trxtime=20150907113716&ro_BankOrderId=2839930044&rb_BankId=CMBCHINA-NET&rp_PayDate=20150907113404&rq_CardNo=&rq_SourceFee=0.0&rq_TargetFee=0.0&hmac=a09229e0e988f40e9c9346d6808dfda0")
    # print yeepay_notify.real_success()
