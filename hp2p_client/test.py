import threading
import schedule
import time
import socket

is_run_scheduler = True


def run_recovery_scheduler():
    print("[RecoveryScheduler] Start...", flush=True)
    t = threading.Thread(target=run_pending, daemon=True)
    t.start()


def checked_primary_connection():
    print('\n++++++++ checked_primary_connection.')


def checked():
    print('\n!!!!!!!!!!!!!!!!!!!!!!!.')


def run_pending():
    while is_run_scheduler:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('127.0.0.1', 9071))
    print('start udp server.')
    while True:
        data, addr = sock.recvfrom(1024)
        data = data.decode()
        print(data)
    # run_recovery_scheduler()
    #
    # while True:
    #     a = input('!!')
    #     if a == '1':
    #         print('clear')
    #         schedule.clear()
    #     elif a == '2':
    #         schedule.every(2).seconds.do(checked_primary_connection)
    #     elif a == '3':
    #         schedule.every(5).seconds.do(checked)
