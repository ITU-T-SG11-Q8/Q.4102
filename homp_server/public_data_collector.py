import time

import socket
import schedule
import argparse
import json
import requests

from database.db_connector import DBConnector
from database.db_manager import DBManager

get_interval = None
send_interval = None
offset_index = 0

public_data_url = 'http://openapi.airkorea.or.kr/openapi/services/rest/ArpltnInforInqireSvc/getCtprvnMesureLIst?' \
                  'itemCode=PM10&dataGubun=HOUR&pageNo=1&_returnType=json&ServiceKey=' \
                  'so4KaXm4eGJFU6f7%2FJeJb9UdaSBVXCKrvKW3n%2BMBPh6N3JNJyq2SybG24knfxlEUbBxbw3u7mkxNozuzsVM%2Fng%3D%3D'

public_data_url_get_one = public_data_url + '&numOfRows=1'


class PeerTcpConnection:
    def __init__(self, peer_id, peer_port):
        self._peer_ip = peer_id
        self._peer_port = peer_port
        self._sock = None

    def closed_connection(self):
        if self._sock is not None:
            self._sock.close()
            self._sock = None

    def send_message(self, message):
        send_connection = self.get_connection()
        try:
            if send_connection is not None:

                bytes_body = bytes(json.dumps(message), encoding='utf=8')
                bytes_length = len(bytes_body).to_bytes(4, 'little')
                send_connection.sendall((bytes_length + bytes_body))
                print('[Public Data Collector] Send Message.')
            else:
                print('[Public Data Collector] Connection is None.')
        except Exception as send_e:
            self.closed_connection()
            print('[Public Data Collector] ', send_e)

    def get_connection(self):
        try:
            if self._sock is None:
                self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._sock.connect((self._peer_ip, self._peer_port))
        except:
            self.closed_connection()

        return self._sock


def init_job():
    try:
        response = requests.get(public_data_url)
        if response.status_code == 200:
            json_data = response.json()
            json_data_get_list = json_data.get('list')

            if json_data_get_list is not None and len(json_data_get_list) > 0:
                db_connector = DBConnector()
                try:
                    for json_data_item in json_data_get_list:
                        data_time = json_data_item.get('dataTime')
                        query = "INSERT INTO public_data (data_time, pm10_data, updated_at) VALUES (%s, %s, NOW()) " \
                                "ON DUPLICATE KEY UPDATE updated_at=NOW()"
                        db_connector.insert(query, (data_time, json.dumps(json_data_item)))

                    db_connector.commit()
                    print("[Public Data Collector] INTI Public Data.")
                except:
                    db_connector.rollback()

    except Exception as init_e:
        print(init_e)


def get_job():
    try:
        response = requests.get(public_data_url_get_one)
        if response.status_code == 200:
            json_data = response.json()
            json_data_list = json_data.get('list')
            json_data_item = None
            if len(json_data_list) > 0:
                json_data_item = json_data_list[0]

            if json_data_item is not None:
                db_connector = DBConnector()
                try:
                    query = "INSERT INTO public_data (data_time, pm10_data, updated_at) VALUES (%s, %s, now()) " \
                            "ON DUPLICATE KEY UPDATE updated_at=NOW()"
                    db_connector.insert(query, (json_data_item.get('dataTime'), json.dumps(json_data_item)))
                    db_connector.commit()
                    print("[Public Data Collector] GET Public Data.")
                except:
                    db_connector.rollback()

    except Exception as get_e:
        print(get_e)


def send_job(connection: PeerTcpConnection):
    try:
        global offset_index
        db_connector = DBConnector()
        query = "SELECT pm10_data, data_time FROM public_data ORDER BY data_time DESC LIMIT %s,1"
        result = db_connector.select_one(query, (offset_index,))
        if result is None or len(result) < 1:
            offset_index = 0
            result = db_connector.select_one(query, (offset_index,))

        offset_index += 1

        if result is not None:
            # json_data = json.dumps(result.get('pm10_data'))
            connection.send_message(result.get('pm10_data'))

    except Exception as send_e:
        print(send_e)


def args_parsing():
    parser = argparse.ArgumentParser(
        prog="Public Data Collector"
    )

    parser.add_argument("-ip", help="전송 대상의 IP 정보를 설정한다.", dest="ip", type=str,
                        metavar="Send Peer IP", required=True)
    parser.add_argument("-port", help="전송 대상의 Port 정보를 설정한다.", dest="port", type=int,
                        metavar="Send Peer Port", required=True)
    parser.add_argument("-gi", help="데이터 수집 주기(분) 설정한다.", dest="get_interval", type=int, default=10,
                        metavar="Get Interval", required=False)
    parser.add_argument("-si", help="데이터 전송 주기(초) 설정한다.", dest="send_interval", type=int, default=3,
                        metavar="Send Interval", required=False)

    return parser.parse_args()


if __name__ == '__main__':
    arg_results = args_parsing()

    try:
        peer_tcp_connection = PeerTcpConnection(arg_results.ip, arg_results.port)

        db_manager = DBManager()
        db_init = db_manager.init_public_data()

        init_job()

        schedule.every(arg_results.get_interval).minutes.do(get_job)
        schedule.every(arg_results.send_interval).seconds.do(send_job, peer_tcp_connection)
        print("[Public Data Collector] Start...", flush=True)

        while True:
            schedule.run_pending()
            time.sleep(1)

    except Exception as e:
        print(e)
        print('Bye...')
