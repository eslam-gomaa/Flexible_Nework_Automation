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

    print('')
    connection.print("Testing using conditions...")
    if not connection.shell(cmd="sh version", search='Cisco IOS Software, IOSv Software')['search_found?']:
        connection.print("This device is NOT a Cisco Router, I'll assume it's a Switch", level='warn')
        connection.shell(cmd='show ip int br', search='(?:[0-9]{1,3}\.){3}[0-9]{1,3}', print_json=True)

    connection.print('Testing: condition based on exit_code; running command')
    if connection.shell(cmd="show ip int br", print_json=True)['exit_code'] == 0:
        connection.print("The command run successfully with exit_code 0", level='info')

    # ******************************* End ***************************************

    hosts['hosts_number'] -= 1
    print('')
    connection.close()
