from main import SSH_Connect
from main import hosts

username = 'orange'
password = 'cisco'
enable_pwd = 'cisco'

# ****************************** Start **************************************

hosts = hosts()

print("[ INFO ] Number of hosts left: " + str(hosts['hosts_number']))
for host in hosts['hosts']:

    connection = SSH_Connect(host, username, password, allow_agent=True)
    connection.shell(cmd='enable\n' + enable_pwd)

    connection.print("Let's begin ^_^ ", level='info')
    if connection.shell(cmd="sh version", search='Cisco IOS Software, vios_l2 Software')['search_found?']:

        connection.print("This device is a Cisco Switch, Let's create a VLAN !", level='warn')
        connection.shell(cmd_from_file='./conf_file.txt',)

        connection.print("Let's check that the vlan exists ! & see some output", level='warn')
        if connection.shell(cmd="sh vlan br", print_stdout=True,print_json=True, search='[0-9]+  Dev')['search_found?']:
            connection.print("VLAN exists - We're Done ! ^_^")

    # ******************************* End ***************************************

    hosts['hosts_number'] -= 1
    print('')
    connection.close()
