import pymysql

connect = pymysql.connect(host="localhost", 
                                       db="hp2p",
                                       user="root", password="wkdtjqdl",
                                       charset='utf8', cursorclass=pymysql.cursors.DictCursor)
print(connect)
 

