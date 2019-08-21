class Properties:
    def __init__(self):
        self.tcp_server_ip = '127.0.0.1'
        self.tcp_server_port = 9999

        self.toms_url = 'http://localhost:8081'
        self.expires = 5000
        self.type = 'code'
        self.sub_type = 'tree'
        self.auth_type = 'open'
        # self.address = 'tcp://192.168.0.25:9999'

        self.max_capacity = 10
        self.max_out_candidate = 5
        self.max_in_candidate = 5

        self.ttl = 5
        self.conn_num = 5
