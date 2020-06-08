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

    connection.shell(cmd='show vlan br', print_stdout=True, print_json=False, search='[0-9]+  Dev')
    connection.shell(cmd='show ip int br', print_stdout=True, print_json=False, search='[0-9]+  Dev')

#******************************* End ***************************************

    hosts['hosts_number'] -= 1
    print('')
    connection.close()
