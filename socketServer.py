import logging
from debug import INFO, DEBUG
from websocket_server import WebsocketServer
import json


# Callback functions
def new_client(client, server):
    INFO('New client ' + str(client['address'][0]) + ':' + str(client['address'][1]) + ' has joined.')


def client_left(client, server):
    INFO('Client ' + str(client['address'][0]) + ':' + str(client['address'][1]) + ' has left.')


def message_received(client, server, message):
    DEBUG('Message has been received from ' + str(client['address'][0]) + ':' + str(client['address'][1]))
    try:
        message_dict = json.loads(message)
        if message_dict['type'] == 'guide_info':
            try:
                with open('./guide_info.json', mode='w') as f:
                    f.write(message)
            except AttributeError:
                INFO('faild to get color data')
    except json.JSONDecodeError:
        INFO('faild to decode message to json')


# Main
if __name__ == "__main__":
    server = WebsocketServer(port=9001, host='192.168.100.122', loglevel=logging.INFO)
    server.set_fn_new_client(new_client)
    server.set_fn_client_left(client_left)
    server.set_fn_message_received(message_received)
    
    server.run_forever()
