set /p id=overlayID:
UPREPC.exe -p peer3 -o 30002 -l 192.168.10.10:23324 -s http://192.168.10.10:9100/oms -k 512 -v %id% -h -c no -m 23335