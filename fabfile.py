#-*- coding:utf-8 -*-
from fabric import Connection as connection, task
from invoke import Responder

#hosts = ( 'k8s-worker-node1', )
hosts = (
        'k8s-worker-node1',
        'k8s-worker-node2',
        'k8s-worker-node3',
        'k8s-worker-node4',
        'k8s-worker-node5',
        'k8s-worker-node6',
        'k8s-worker-node7',
        'k8s-worker-node8',
        'k8s-worker-node9',
        'k8s-worker-node10',
        'k8s-worker-node11',
        'k8s-worker-node12'
        )


'''
ssh 자동연결이 되어 있지 않을 경우, 아래처럼 해 준다.
ctx = Connection(host='u2pia.duckdns.org', user='pi', connect_kwargs={"password":"wkdtjqdl"})


'''


@task
def test(ctx):
    for  host in hosts:
        try:
            with connection(host=host, user='whyun') as c:
                #c.run('ls -la')
                c.run('hostname')
        except:
            print('error')



@task
def deploy(ctx):
    for  host in hosts:
        try:
            with connection(host=host, user='whyun') as c:
                #c.run('ls -la')
                c.run('hostname')
                c.run('mkdir -p workspace')
                c.run('cd workspace; git clone https://github.com/superwhyun/HP2P', pty=True, watchers=[github_username, github_password])
        except:
            print('error')

@task
def update(ctx):
    for  host in hosts:
        try:
            with connection(host=host, user='whyun') as c:
                #c.run('ls -la')
                c.run('hostname')
                c.run('mkdir -p workspace')
                c.run('cd workspace/HP2P; git pull', pty=True, watchers=[github_username, github_password])
        except:
            print('error')



@task
def start(ctx):
    for  host in hosts:
        try:
            with connection(host=host, user='whyun') as c:
                #c.run('ls -la')
                c.run('hostname')
        except:
            print('error')



github_username = Responder(
        pattern=r'Username for \'https://github.com\':',
        response='superwhyun\n', )
github_password = Responder(
        pattern=r'Password for \'https://superwhyun@github.com\':',
        response='Rjwurlxm!1\n', )
