import time
import schedule
import json
import requests
import argparse

from config import OPEN_API
from classes.tcp_connection import TcpConnection
from database.db_connector import DBConnector
from database.db_manager import DBManager

offset_index = 0


def call_api_and_save_data(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            json_data = response.json()
            json_data_get_list = json_data.get('list')

            if json_data_get_list is not None and len(json_data_get_list) > 0:
                db_connector = DBConnector()
                try:
                    for json_data_item in json_data_get_list:
                        data_time = json_data_item.get('dataTime')
                        query = "INSERT INTO fine_dust (data_time, pm10_data, updated_at) VALUES (%s, %s, NOW()) " \
                                "ON DUPLICATE KEY UPDATE updated_at=NOW()"
                        db_connector.insert(query, (data_time, json.dumps(json_data_item)))

                    db_connector.commit()
                    print("[Data Collector] CALL_API_AND_SAVE_DATA.")
                except:
                    db_connector.rollback()

    except Exception as e1:
        print(e1)


def get_today_data(url):
    print("[Data Collector] GET_TODAY_DATA.")
    call_api_and_save_data(url)


def get_current_data(url):
    print("[Data Collector] GET_CURRENT_DATA.")
    call_api_and_save_data(url)


def send_data(connection: TcpConnection, is_shifting_data: bool):
    try:
        global offset_index
        db_connector = DBConnector()
        query = "SELECT pm10_data, data_time FROM fine_dust ORDER BY data_time DESC LIMIT %s,1"
        result = db_connector.select_one(query, (offset_index,))
        if result is None or len(result) < 1:
            offset_index = 0
            result = db_connector.select_one(query, (offset_index,))

        if is_shifting_data:
            offset_index += 1

        if result is not None:
            print(result)
            connection.send_message(result.get('pm10_data'))

    except Exception as send_e:
        print(send_e)


def args_parsing():
    parser = argparse.ArgumentParser(
        prog="Data Collector"
    )
    parser.add_argument("-ip", help="전송 대상의 IP 정보를 설정한다.", dest="target_ip", type=str,
                        metavar="Send Peer IP", required=True)
    parser.add_argument("-port", help="전송 대상의 Port 정보를 설정한다.", dest="target_port", type=int,
                        metavar="Send Peer Port", required=True)
    parser.add_argument("-ci", help="데이터 수집 주기(분) 설정한다.", dest="call_api_interval", type=int, default=10,
                        required=False)
    parser.add_argument("-si", help="데이터 전송 주기(초) 설정한다.", dest="send_interval", type=int, default=10,
                        required=False)
    parser.add_argument("-shifting", help="DB에 저장된 데이터를 순차적으로 제공할지 설정한다.(테스트용)", dest="is_shifting_data", type=bool,
                        default=False, required=False)
    return parser.parse_args()


if __name__ == '__main__':
    service_key = OPEN_API['SERVICE_KEY']
    data_url = 'http://openapi.airkorea.or.kr/openapi/services/rest/ArpltnInforInqireSvc/getCtprvnMesureLIst?' \
               'itemCode=PM10&dataGubun=HOUR&pageNo=1&_returnType=json&ServiceKey=' + service_key
    data_url_get_one_row = data_url + '&numOfRows=1'

    try:
        arg_results = args_parsing()

        peer_tcp_connection = TcpConnection(arg_results.target_ip, arg_results.target_port)
        db_manager = DBManager()
        db_init = db_manager.init()
        get_today_data(data_url)

        schedule.every(arg_results.call_api_interval).minutes.do(get_current_data, data_url_get_one_row)
        schedule.every(arg_results.send_interval).seconds.do(send_data,
                                                             peer_tcp_connection, arg_results.is_shifting_data)
        print("[Data Collector] Start...", flush=True)

        while True:
            schedule.run_pending()
            time.sleep(1)

    except Exception as e:
        print(e)
        print('Bye...')
