#!/usr/bin/env python
# --coding:utf-8--

from http.server import BaseHTTPRequestHandler, HTTPServer
from os import path
import json
from urllib import request, parse


APP_ID = "cli_9f8855db29bc100b"
APP_SECRET = "CDpPfa4AG8HT7FxmfXxSSxT2uqGxmGGQ"
APP_VERIFICATION_TOKEN = "wKJVm4rSlxvEiaqwJeHDlfUo3aPbt3il"

class RequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        # �ѪR?�D body
        req_body = self.rfile.read(int(self.headers['content-length']))
        obj = json.loads(req_body.decode("utf-8"))
        print(req_body)

        # ��? verification token �O�_�ǰt�Atoken ���ǰt?��?�^?�}�D?��??���x
        token = obj.get("token", "")
        if token != APP_VERIFICATION_TOKEN:
            print("verification token not match, token =", token)
            self.response("")
            return

        # ���u type ?�z���P?���ƥ�
        type = obj.get("type", "")
        if "url_verification" == type:  # ???�D URL �O�_����
            self.handle_request_url_verify(obj)
        elif "event_callback" == type:  # �ƥ�^?
            # ?���ƥ�?�e�M?���A�}?���??�z�A��?�u?�`?�󾹤H���e�������ƥ�
            event = obj.get("event")
            if event.get("type", "") == "message":
                self.handle_message(event)
                return
        return

    def handle_request_url_verify(self, post_obj):
        # ��?��^ challenge �r�q?�e
        challenge = post_obj.get("challenge", "")
        rsp = {'challenge': challenge}
        self.response(json.dumps(rsp))
        return

    def handle_message(self, event):
        # ��?�u?�z text ?�������A��L?����������
        msg_type = event.get("msg_type", "")
        if msg_type != "text":
            print("unknown msg_type =", msg_type)
            self.response("")
            return

        # ?��?���� API ���e�A���n?�� API ?��??�Gtenant_access_token
        access_token = self.get_tenant_access_token()
        if access_token == "":
            self.response("")
            return

        # �󾹤H echo ���쪺����
        self.send_message(access_token, event.get("open_id"), event.get("text"))
        self.response("")
        return

    def response(self, body):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(body.encode())

    def get_tenant_access_token(self):
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal/"
        headers = {
            "Content-Type" : "application/json"
        }
        req_body = {
            "app_id": APP_ID,
            "app_secret": APP_SECRET
        }

        data = bytes(json.dumps(req_body), encoding='utf8')
        req = request.Request(url=url, data=data, headers=headers, method='POST')
        try:
            response = request.urlopen(req)
        except Exception as e:
            print(e.read().decode())
            return ""

        rsp_body = response.read().decode('utf-8')
        rsp_dict = json.loads(rsp_body)
        code = rsp_dict.get("code", -1)
        if code != 0:
            print("get tenant_access_token error, code =", code)
            return ""
        return rsp_dict.get("tenant_access_token", "")

    def send_message(self, token, open_id, text):
        url = "https://open.feishu.cn/open-apis/message/v4/send/"

        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token
        }
        req_body = {
            "open_id": open_id,
            "msg_type": "text",
            "content": {
                "text": text
            }
        }

        data = bytes(json.dumps(req_body), encoding='utf8')
        req = request.Request(url=url, data=data, headers=headers, method='POST')
        try:
            response = request.urlopen(req)
        except Exception as e:
            print(e.read().decode())
            return

        rsp_body = response.read().decode('utf-8')
        rsp_dict = json.loads(rsp_body)
        code = rsp_dict.get("code", -1)
        if code != 0:
            print("send message error, code = ", code, ", msg =", rsp_dict.get("msg", ""))

def run():
    port = 8000
    server_address = ('', port)
    httpd = HTTPServer(server_address, RequestHandler)
    print("start.....")
    httpd.serve_forever()

if __name__ == '__main__':
    run()