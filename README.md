# Hybrid P2P Server/Peer


## Pre-requisite
- mysql(or maria) DBMS

## Installation

### HP2P (Hybrid P2P network)
- HOMS
```
$ cd network/hp2p/homp/_setup
$ pip install -r requirements.txt
```

- HPEER
```
$ cd network/hp2p/hpeer
$ python setup.py install  # install aiortc 
$ pip install -r requirements.txt
```

### MP2P (Mesh-based P2P network)
- MOMS
```
TBD
```
- MPEER
```
TBD
```

---

## Usage

### HP2P (Hybrid P2P network)
- HOMS
```
$ cd network/hp2p/homs
$ python homs_run.py -port=[Server Port] -ws-port=[WebSocket Port]
```

- HPEER
```
$ cd network/hp2p/hpeer
$ python peer_run.py [parameters]


* mandatory
  - connection=[tcp, rtc] 

* optional 
   - id=[peer_id]    
   - owner=[true, false]  
   - overlay=[overlay_id]    
   - title=[title]  
   - desc=[description] 
   - admin-key=[admin_key]   
   - auth-type=[open, closed]   
   - access-key=[access_key]

```

## Usage Examples

### Run HOMS
``` 
 $ python homs_run.py -port=9000 -ws-port=9100
```

### Overlay network creation
* Creation of hybrid overlay network by an Owner
``` 
 $ python hpeer_run.py -id=seeder -connection=tcp -owner=true
 $ python hpeer_run.py -id=TCP-Creator -connection=tcp -owner=true -title="HP2P Overlay TCP"
 $ python hpeer_run.py -id=Creator -connection=tcp -owner=true -title="HP2P Overlay" -gui-port=8091
 $ python hpeer_run.py  -id=Creator -connection=tcp -owner=true -title="HP2P Overlay" -gui-port=8091 -public-port=9001
 $ python hpeer_run.py  -id=Creator -connection=tcp -owner=true -title="HP2P Overlay" -gui-port=8091 -public-port=9001 -uprep-addr=127.0.0.1:30000
```
### Participants of hybrid overlay network
```
 $ python hpeer_run.py -connection=tcp 
 $ python hpeer_run.py -connection=tcp -gui-port=8092
 $ python hpeer_run.py -connection=tcp -gui-port=8093 -uprep-addr=127.0.0.1:9071
 $ python hpeer_run.py -connection=tcp -gui-port=8094 -public-port=9001 -uprep-addr=127.0.0.1:9071
 ```
