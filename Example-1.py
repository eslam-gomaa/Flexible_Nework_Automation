from main import SSH_Connect
from main import import_hosts


############################################
############################################

username    = 'orange'
password    = 'cisco'
enable_pwd  = 'cisco'
hosts_file  = './hosts.txt'

############################################
############################################

hosts = import_hosts(hosts_file)
hosts_left = hosts['hosts_number']

###### ###### ###### ###### ###### ######

for host in hosts['hosts']:
    print("[ INFO ] Number of hosts left: " + str(hosts_left))
    connection = SSH_Connect(host, username, password, allow_agent=True)

    connection.shell(cmd='enable\n' + enable_pwd)

    connection.shell(cmd='sh ip int br', print_json=True)

    #print(connection.shell(cmd= "sh version", print_stdout=False, print_json=True, search='Cisco IOS Software, IOSv Software')['search_found?'])

    if not connection.shell(cmd="sh version", print_stdout=False, print_json=True, search='Cisco IOS Software, IOSv Software')['search_found?']:
        print('[ Notice ] This device is not a Router')

        if not connection.shell(cmd= "sh access-lists", print_stdout=False,print_json=True, search='10 permit 192.168.12.0, wildcard bits 0.0.0.255')['search_found?']:
            print('[Notice ] Adding ACL to permit 192.168.12.0/24')
            connection.shell(cmd= """
            conf t
            access-list 1 permit0000 192.168.12.0 0.0.0.255
            int GigabitEthernet0/1
            ip access-group 1 in
            no shut
            end
            """,
                             print_stdout=False,
                             print_json=True)
        else:
            print("[ Notice ] ACL to permit 192.168.12.0/24 already exists")

    hosts_left -= 1
    print('')
    connection.close()
