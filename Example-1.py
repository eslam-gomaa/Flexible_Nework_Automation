from main import SSH_Connect
from main import hosts


username    = 'orange'
password    = 'cisco'
enable_pwd  = 'cisco'


#****************************** Start **************************************

hosts = hosts()

print("[ INFO ] Number of hosts left: " + str(hosts['hosts_number']))
for host in hosts['hosts']:

    connection = SSH_Connect(host, username, password, allow_agent=True)
    connection.shell(cmd='enable\n' + enable_pwd)

    if not connection.shell(cmd="sh version", print_stdout=False, print_json=True, search='Cisco IOS Software, IOSv Software')['search_found?']:
        connection.print('This device is not a Router', level='info')

        if not connection.shell(cmd="sh access-lists", print_stdout=False, print_json=True,
                                search='10 permit 192.168.12.0, wildcard bits 0.0.0.255')['search_found?']:
            connection.print('Adding ACL to permit 192.168.12.0/24', level='warn')
            connection.shell(cmd="""
                conf t
                access-list 1 permit 192.168.12.0 0.0.0.255
                int GigabitEthernet0/1
                ip access-group 1 in
                no shut
                end
                """,
                             print_stdout=False,
                             print_json=True)
        else:
            connection.print("ACL to permit 192.168.12.0/24 already exists", level='info')


#******************************* End ***************************************

    hosts['hosts_number'] -= 1
    print('')
    connection.close()
