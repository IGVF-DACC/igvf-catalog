import json
import os
import sys

cmd = '''[Unit]
Description=ArangoDB {description}
After=default.target

[Service]
User=ubuntu
Group=ubuntu
Type=simple
ExecStart={arango_cmd}
Restart=on-failure
StandardOutput=file:%h/{name}_systemd.log

[Install]
WantedBy=default.target'''

# assuming cluster nodes are ordered
cluster = json.load(open('../config/production.json'))['cluster']

# 3 first nodes will be selected as agency
agency_ips = cluster[:3]

path = os.path.expanduser('~')


def get_cmds(node_number):
    pwd = path + '/data'
    if node_number >= 2:
        pwd += str(node_number)

    my_ip = cluster[node_number - 1]

    other_agency_endpoints = ''
    for ip in agency_ips:
        if my_ip != ip:
            other_agency_endpoints += '--agency.endpoint tcp://%s:8531 ' % ip

    cluster_agency_endpoints = ''
    for ip in agency_ips:
        cluster_agency_endpoints += '--cluster.agency-endpoint tcp://%s:8531 ' % ip

    # agency
    agency = f'/usr/sbin/arangod -c {pwd}/agent8531/arangod.conf --database.directory {pwd}/agent8531/data --javascript.startup-directory /usr/share/arangodb3/js --javascript.app-path {pwd}/agent8531/apps --log.file {pwd}/agent8531/arangod.log --log.force-direct false --server.jwt-secret-keyfile {pwd}/agent8531/arangod.jwtsecret --javascript.copy-installation true --agency.activate true --agency.my-address tcp://{my_ip}:8531 --agency.size 3 --agency.supervision true --foxx.queues false --server.statistics false {other_agency_endpoints}'

    # dbserver
    dbserver = f'/usr/sbin/arangod -c {pwd}/dbserver8530/arangod.conf --database.directory {pwd}/dbserver8530/data --javascript.startup-directory /usr/share/arangodb3/js --javascript.app-path {pwd}/dbserver8530/apps --log.file {pwd}/dbserver8530/arangod.log --log.force-direct false --server.jwt-secret-keyfile {pwd}/dbserver8530/arangod.jwtsecret --javascript.copy-installation true --cluster.my-address tcp://{my_ip}:8530 --cluster.my-role PRIMARY --foxx.queues false --server.statistics true {cluster_agency_endpoints}'

    # coordinator
    coordinator = f'/usr/sbin/arangod -c {pwd}/coordinator8529/arangod.conf --database.directory {pwd}/coordinator8529/data --javascript.startup-directory /usr/share/arangodb3/js --javascript.app-path {pwd}/coordinator8529/apps --log.file {pwd}/coordinator8529/arangod.log --log.force-direct false --server.jwt-secret-keyfile {pwd}/coordinator8529/arangod.jwtsecret --javascript.copy-installation true --cluster.my-address tcp://{my_ip}:8529 --cluster.my-role COORDINATOR --foxx.queues true --server.statistics true {cluster_agency_endpoints}'

    return agency, dbserver, coordinator


def generate_systemd(node_number, dry_run=False):
    agency, dbserver, coordinator = get_cmds(node_number)

    if dry_run:
        print(cmd.format(arango_cmd=dbserver, name='dbserver',
              description='DBserver process', pwd=path))
        print(cmd.format(arango_cmd=coordinator, name='coordinator',
              description='Coordinator process', pwd=path))
        if node_number <= 3:
            print(cmd.format(arango_cmd=agency, name='agency',
                  description='Agency process', pwd=path))
    else:
        with open('./arango_dbserver.service', 'w') as dbserver_systemd:
            dbserver_systemd.write(cmd.format(
                arango_cmd=dbserver, name='dbserver', description='DBserver process', pwd=path))

        with open('./arango_coordinator.service', 'w') as coordinator_systemd:
            coordinator_systemd.write(cmd.format(
                arango_cmd=coordinator, name='coordinator', description='Coordinator process', pwd=path))

        if node_number <= 3:
            with open('./arango_agency.service', 'w') as agency_systemd:
                agency_systemd.write(cmd.format(
                    arango_cmd=agency, name='agency', description='Agency process', pwd=path))


if __name__ == '__main__':
    # Get the number of input arguments.
    num_args = len(sys.argv)

    if num_args < 1:
        print('Node number required (1, 2, 3, or 4). Usage: $ python3 generate_systemd.py <node_number>')
        exit(1)

    try:
        node_number = int(sys.argv[1])
    except:
        print('Invalid node number. Available: (1, 2, 3, or 4). Usage: $ python3 generate_systemd.py <node_number>')
        exit(1)

    generate_systemd(node_number)

    print("1. Move service files to system's service folder: $ sudo cp *service /etc/systemd/system/")
    print('2. Reload systemd: $ sudo systemctl daemon-reload')
    print('\n3. Start services:')
    print('\t3.1. sudo systemctl start arango_dbserver ')
    print('\t3.2. sudo systemctl start arango_coordinator ')
    if node_number <= 3:
        print('\t3.3. sudo systemctl start arango_agency ')
