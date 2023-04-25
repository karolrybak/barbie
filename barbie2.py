#!/usr/bin/env python3

import logging
from getpass import getpass
from argparse import ArgumentParser
import slixmpp
import openai
from collections import deque
import os
import sys
import requests
import json
import validators
import html
import urllib
import base64

openai.api_key = "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"

chat_context = {}


class MUCBot(slixmpp.ClientXMPP):
    previous_message = ''

    def __init__(self, jid, password, room, nick):
        slixmpp.ClientXMPP.__init__(self, jid, password)

        self.room = room
        self.nick = nick
        self.previous_message = ''
        self.add_event_handler("session_start", self.start)
        self.add_event_handler("groupchat_message", self.muc_message)
        self.add_event_handler("message", self.muc_directmessage)

    async def start(self, event):
        await self.get_roster()
        self.send_presence()
        self.plugin['xep_0045'].join_muc(self.room, self.nick)

    def get_chatgpt_response(self, text, user, remberChat=True):
        print("Getting CHATGPT RESPONSE")
        print(text)
        print(user)

        context = []
        if not user in chat_context:
            chat_context[user] = deque(maxlen=10)

        if remberChat == True:
            chat_context[user].append({"role": "user", "content": text})
            context = chat_context[user]
        else:
            context = [{"role": "user", "content": text}]

        # response = openai.ChatCompletion.create(
            # model="gpt-3.5-turbo",
            # messages=[*context] + [
            # {"role": "system", "content": "Jesteś genialną asystentką"},
            # {'role': 'user', 'content': "Masz na imię Barbie"},
            # {'role': 'user', 'content': "Dodaj do odpowiedzi zabawną historię"},
            # {'role': 'user', 'content': "odpowiedź skróć do 7 lini tekstu"},
            # {'role': 'user', 'content': "pisz wierszem i na końcu każdej lini tekstu dodaj emoji"},
            # {'role': 'user', 'content': "na końcu emoji z serduszkami i całusami"},
            # ]
        # )


# Dodaj do odpowiedzi zabawną historię
# odpowiedź skróć do 7 lini tekstu
# pisz wierszem i na końcu każdej lini tekstu dodaj emoji
# na końcu emoji z serduszkami i całusami

        # messages = [
        #     {"role": "system", "content": "Opowiadasz historie fantasy"},
        #     {'role': 'user', 'content': "Napisz co najmniej 5 lini tekstu"},
        #     {'role': 'user', 'content': "Unikaj odpowiedzi i pisz długie ciekawe historie o czarodziejach i trollach"},
        #     {'role': 'user', 'content': "Nie odpowiadaj na nic tylko pisz żarty "},
        #     {'role': 'user', 'content': "Pisz wierszem i dodawaj dużo emoji"}
        # ] + [*context]

        messages = [
            {"role": "system", "content": "You are helping with programming"},
            # {'role': 'user', 'content': "Write as simple code as posiible and don't add commments"},
            # {'role': 'user', 'content': "Przetłumacz na polski sformatuj w akapity i dodaj emoji"},
        ] + [*context]

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        result = ''
        for choice in response.choices:
            result += choice.message.content

        print(result)

        if remberChat == True:
            chat_context[user].append({"role": "assistant", "content": result})

        print(chat_context[user])
        return result

    def send_image(self, data):
        # Wysyłanie obrazka na kanał do którego jesteś połączony
        file_name = 'generated_image.png'
        headers = {
            'Content-Disposition': 'attachment; filename="{}"'.format(file_name)}
        response = requests.post('http://{}:5280/upload/{}'.format(self.server, self.room),
                                 headers=headers,
                                 data=data)

        if response.status_code == 200:
            print("Image sent successfully!")
        else:
            print("Image sending failed!")

    def muc_directmessage(self, msg):
        print(msg)
        text = msg['body'].strip()
        user = str(msg['from'])
        print("user" + user)

        if text.startswith('zapomnij'):
            print("zapominam: " + str(msg['from']))
            chat_context[msg['from']] = deque(maxlen=10)
            reply = self.make_message(
                msg['from'], "Zapominam nasz czat" + user)
        elif text.startsWith('obrazek'):
            file_name = os.path.basename(self.file_path)
            file_size = os.path.getsize(self.file_path)
            file_content = ''

            with open(self.file_path, 'rb') as file:
                file_content = base64.b64encode(file.read()).decode('utf-8')

            iq = self.Iq()
            iq['type'] = 'set'
            iq['to'] = self.recipient_jid
            data = ET.Element('data', xmlns='urn:xmpp:bob')
            data.attrib['cid'] = f"{file_name}@bob.xmpp.org"
            data.attrib['type'] = 'application/octet-stream'
            data.attrib['max_age'] = '86400'
            data.text = file_content

            iq.set_payload(data)
            # await iq.send()

            message = self.Message()
            message['to'] = self.recipient_jid
            message['type'] = 'chat'
            message['body'] = f"Sending file: {file_name} (size: {file_size} bytes)"
            message.send()
        elif text.startswith('restart'):
            print("restart")
            python = sys.executable
            os.execl(python, python, *sys.argv)
        elif msg['type'] == 'chat':
            print("thinking")
            reply = self.make_message(
                msg['from'], self.get_chatgpt_response(text, user))
            reply['type'] = 'chat'
            reply.send()

    def muc_message(self, msg):
        text = msg['body']
        user = str(msg['from'])
        stanza = msg.get_stanza_values()
        print('user:' + user)

        print('last message ' + str(self.previous_message))

        if validators.url(text):
            print(text)
            print(urllib.parse.quote_plus(text))
            url = 'https://api.smmry.com/&SM_API_KEY=C5BEFF4235&SM_WITH_BREAK=true&SM_WITH_ENCODE=true&SM_LENGTH=20&SM_URL=' + text
            result = requests.get(url, timeout=20)
            print(result)
            data = json.loads(result.text)

            print(data)
            response = data['sm_api_content']
            print(response)
            response = html.unescape(response.replace('[BREAK]', "\n"))

            response = self.get_chatgpt_response(
                "przetłumacz na polski, skróć tekst do 10 zdań i dodaj akapity do tekstu: " + response, user, remberChat=False)

            self.send_message(mto=msg['from'].bare,
                              mbody=response,
                              mtype='groupchat')

        elif text.lower().startswith(self.nick):
            text = text[len(self.nick):].strip()
            print(text)
            if text == "":
                msg = self.previous_message
                stanza = msg.get_stanza_values()
                user = stanza['mucroom']
                text = msg['body']
                print('sending ' + str(msg['body']))
                response = self.get_chatgpt_response(
                    text.replace(self.nick, ''), user)
            elif text.startswith('zapomnij'):
                print("zapominam " + str(user))
                chat_context[user] = deque(maxlen=10)
                response = 'zapominam nasz chat ' + user

            elif text.startswith('restart'):
                print("restart")
                python = sys.executable
                os.execl(python, python, *sys.argv)
            else:
                print("thinking")
                response = self.get_chatgpt_response(
                    text.replace(self.nick, ''), user)

            self.send_message(mto=msg['from'].bare,
                              mbody=response,
                              mtype='groupchat')

        self.previous_message = msg

        # if (msg.encrypted):
        #     omemo_session = self['xep_0384'].get_omemo_session(
        #         msg['from'].bare())
        #     omemo_keys = omemo_session.get_bundle()
        #     decrypted_text = omemo.decrypt(bytes.fromhex(
        #         msg['body']), omemo_keys).decode('utf-8')
        #     print(decrypted_text)

    def muc_online(self, presence):
        if presence['muc']['nick'] != self.nick:
            self.send_message(mto=presence['from'].bare,
                              mbody="Hello, %s %s" % (presence['muc']['role'],
                                                      presence['muc']['nick']),
                              mtype='groupchat')


if __name__ == '__main__':
    # Setup the command line arguments.
    parser = ArgumentParser()

    # Output verbosity options.
    parser.add_argument("-q", "--quiet", help="set logging to ERROR",
                        action="store_const", dest="loglevel",
                        const=logging.ERROR, default=logging.INFO)
    parser.add_argument("-d", "--debug", help="set logging to DEBUG",
                        action="store_const", dest="loglevel",
                        const=logging.DEBUG, default=logging.INFO)

    # JID and password options.
    parser.add_argument("-j", "--jid", dest="jid",
                        help="JID to use")
    parser.add_argument("-p", "--password", dest="password",
                        help="password to use")
    parser.add_argument("-r", "--room", dest="room",
                        help="MUC room to join")
    parser.add_argument("-n", "--nick", dest="nick",
                        help="MUC nickname")

    args = parser.parse_args()

    # Setup logging.
    logging.basicConfig(level=args.loglevel,
                        format='%(levelname)-8s %(message)s')

    if args.jid is None:
        args.jid = input("Username: ")
    if args.password is None:
        args.password = getpass("Password: ")
    if args.room is None:
        args.room = input("MUC room: ")
    if args.nick is None:
        args.nick = input("MUC nickname: ")

    # Setup the MUCBot and register plugins. Note that while plugins may
    # have interdependencies, the order in which you register them does
    # not matter.
    xmpp = MUCBot(args.jid, args.password, args.room, args.nick)
    xmpp.register_plugin('xep_0030')  # Service Discovery
    xmpp.register_plugin('xep_0045')  # Multi-User Chat
    xmpp.register_plugin('xep_0199')  # XMPP Ping
    # xmpp.register_plugin('xep_0030')
    # xmpp.register_plugin('xep_0066') # OOB

    # xmpp.register_plugin('xep_0096')  # file transfer

    # xmpp.register_plugin('xep_0384')  # OMEMO Encryption

    # Connect to the XMPP server and start processing XMPP stanzas.
    xmpp.connect()
    xmpp.process()
