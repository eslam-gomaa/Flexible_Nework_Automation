from main import SSH_Connect


############################################
############################################

username    = 'orange'
password    = 'cisco'
enable_pwd  = 'cisco'
hosts_file  = './hosts.txt'

############################################
############################################

def hosts_from_file(file):
    hosts_file_ =  open(file, 'r')
    h1 =  hosts_file_.read().split("\n")
    info = {}
    info['hosts'] = [string for string in h1 if string != '']
    info['hosts_number'] = len(info['hosts'])
    return info

hosts = hosts_from_file(hosts_file)
hosts_left = hosts['hosts_number']


###### ###### ###### ###### ###### ######

for host in hosts['hosts']:
    print("[ INFO ] Number of hosts left: " + str(hosts_left))
    connection = SSH_Connect(host, username, password, allow_agent=True)

    connection.shell(cmd='enable\n' + enable_pwd)
    check_cmd = connection.shell(cmd='sh version1', print_json=True)

    connection.shell(cmd="sh version", print_stdout=True, print_json=True)


    hosts_left -= 1
    print('')
    connection.close()

