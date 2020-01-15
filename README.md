# Hybrid P2P Server/Peer

## HOMS

### pre-requisite
- mysql dbms (or maria db)

### installation
>$ cd homp_server

>$ pip install -r requirements.txt

### usage

>$ python homs_run.py

## HPEER

### usage

```
필수 항목
-connection=[tcp, rtc]   => 연결 방식를 설정한다. (필수 항목)

선택 항목
-id=[peer_id]   => Peer ID를 설정한다. (Optional ,자동 생성)
-password=[auth_password]   => Peer Auth Password 을/를 설정한다. (Optional , 자동 생성)
-owner=[true, false]   => 채널 생성을 요청한다. (Optional , Default=False)
-overlay=[overlay_id]   => 참가할 Overlay ID를 설정한다. (Optional , Default=최근 생성된 채널)
-title=[title]   => 채널 타이틀을 설정한다. (Optional , Default=No Title)
-desc=[description]   => 채널 설명을 설정한다. (Optional , Default=Description)
-admin-key=[admin_key]   => 채널 Admin Key 을/를 설정한다. (Optional , 자동 생성)
-auth-type=[open, closed]   => 채널 Auth Type 을/를 설정한다. (Optional , Default=open)
-access-key=[access_key]   => 채널 Access Key 을/를 설정한다. (Optional , Default=etri), 채널의 Auth Type 이 closed 일 경우에만 유효함. 채널 생성 및 참가 시 사용
```

### usage example
* Overlay Owner
 >$ python client.py -id=seeder -connection=tcp -owner=true

* Overlay Participants

  * Join to latest channel (For easy testing)
   >$ python client.py 


