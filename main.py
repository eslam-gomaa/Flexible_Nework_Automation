import paramiko
import sys
import time
import os
import socket
from pygments import highlight, lexers, formatters
import re
import json
import argparse


# pip install pygments
# pip install paramiko


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    GRAY = "\033[1;30;40m"


parser = argparse.ArgumentParser(description='')
parser.add_argument('-f', '--file', type=str, required=False, metavar='', help='provide the hosts file')
results = parser.parse_args()
hosts_file = results.file
if hosts_file is None:
    print("[ Error ] " + bcolors.FAIL + "--file option must be specified" + bcolors.ENDC)
    print('')
    parser.print_help(sys.stderr)
    exit(1)
if not os.path.isfile(hosts_file):
    print("[ Error ] " + bcolors.FAIL + "({}) is NOT a File".format(hosts_file) + bcolors.ENDC)
    print('')
    parser.print_help(sys.stderr)
    exit(1)


def hosts(file=hosts_file):
    hosts_file_ = open(file, 'r')
    h1 = hosts_file_.read().split("\n")
    info = {}
    info['hosts'] = [string for string in h1 if string != '']
    info['hosts_number'] = len(info['hosts'])
    return info


def get_stderr(string, search='\^'):
    """
    function to search for keywords inside of text and to get several lines of the matched keywords
    so that it can be represented as STDERR
    :param string: string text to search for an error keyword
    :param search: Regex search in the text provided in "String" Parameter'
    :return: dict consists of 2 keys {list: list of matched lines (can contain empty lines), string: matched lines as a string}
    """
    n = 0
    string_list_with_number = {}
    found_with_number = {}
    string_list = string.split("\n")  # split the text into lines separated by "new line"
    for line in string_list:  # create a dict "string_list_with_number" which consists of line number & text of each line
        n += 1
        string_list_with_number[n] = line
        found = re.findall("{}.*$".format(search), line)  # searches the keyword inside the lines
        found_with_number[
            n] = found  # dict "found_with_number" consists of line number & matched lines; lines that does
        # not match the search will be empty arr like: {1: [], 2: [], 3: ['% bla bla], 4: []}

    err_lines = []
    for key, value in found_with_number.items():  # iterate over matched lines in the dict "found_with_number"
        if value:
            err_lines.append(key)  # save the line number of the matched lines in "err_lines" list

    result = []
    lines_to_print = []
    for num in err_lines:
        num -= 1  # get a previous line (to get the command line)
        for i in range(6):  # get 6 lines after the error detected line
            lines_to_print.append(
                num + i)  # append the result to "lines_to_print" dict (which contains needed line numbers)
    try:
        for i in list(set(lines_to_print)):  # list(set(lines_to_print)) --> to get rid of duplicates
            result.append(string_list_with_number[i])  # save the matched lines (strings) to "result" list

    except KeyError:
        return
    finally:
        dict = {'list': result, 'string': '\n'.join(result)}
        return dict


class SSH_Connect:
    """
    Class to Connect & execute commands to hosts/devices via ssh
    """

    def __init__(self, host, user, password, port=22, ssh_timeout=10, allow_agent=False):
        self.info = {}
        self.hosts = None
        self.host = host
        self.user = user
        self.password = password
        self.port = port
        self.ssh_timeout = ssh_timeout
        self.is_connected = False
        self.channel = None

        print("[ INFO ] " + bcolors.WARNING + "Trying to connect to (%s)" % self.host + bcolors.ENDC)
        i = 1
        while True:
            try:
                self.ssh = paramiko.SSHClient()
                self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self.ssh.connect(self.host, self.port, self.user, self.password, timeout=self.ssh_timeout,
                                 allow_agent=allow_agent, look_for_keys=False)
                self.is_connected = True
                connected_msg = ("[ INFO ] " + bcolors.OKGREEN + "Connected to (%s)" % self.host + bcolors.ENDC)
                print(connected_msg)

                self.channel = self.ssh.invoke_shell()
                output = self.channel.recv(9999)
                self.channel.send_ready()
                time.sleep(1)
                break
            except paramiko.AuthenticationException as e:
                print(
                    "[ ERROR ] " + bcolors.FAIL + "Authentication failed when connecting to %s" % self.host + bcolors.ENDC)
                print("\t --> " + str(e))
                print("\t --> (%s) " % self.host + bcolors.FAIL + "Skipped" + bcolors.ENDC)
                print("")
                break
            except socket.gaierror as e:
                print(
                    "[ ERROR ] " + bcolors.FAIL + "Could not resolve hostname (%s) Name or service not known" % self.host + bcolors.ENDC)
                print("\t --> " + str(e))
                print("\t --> (%s) " % self.host + bcolors.FAIL + "Skipped" + bcolors.ENDC)
                print("")
                break
            except (paramiko.ssh_exception.NoValidConnectionsError, paramiko.SSHException, socket.error)  as e:
                print(
                    "[ ERROR ] " + bcolors.FAIL + "Not able to establish ssh connection with %s" % self.host + bcolors.ENDC + " , Trying again...")
                print("\t --> " + str(e))
                i += 1
                time.sleep(1)
                if i == 5:
                    print("[ ERROR ] " + bcolors.FAIL + "Could not connect to %s. Giving up" % self.host + bcolors.ENDC)
                    print("\t --> (%s) " % self.host + bcolors.FAIL + "Skipped" + bcolors.ENDC)
                    print("")
                    break

    def print(self, msg, level='info', force=False):
        """
        Method to Print with different print Levels ('info', 'warn', 'fail')
        :param force: by default it NOT print if the failed to connect to the host, use this option to print anyway
        :param level: info (green color), warn(yellow color), fail(red color)
        :param msg: The message to be printed
        :return:
        """
        color = None
        start = None
        if level == 'info':
            color = bcolors.OKGREEN
            start = bcolors.GRAY + "-- INFO --" + bcolors.ENDC
        elif level == 'warn':
            color = bcolors.WARNING
            start = bcolors.GRAY + "-- WARNING --" + bcolors.ENDC
        elif level == 'fail':
            color = bcolors.FAIL
            start = bcolors.GRAY + "[FAIL]" + bcolors.ENDC
        else:
            print(
                bcolors.FAIL + " Supported print level options are: ['info', 'warn', 'fail'] - Your input: ({})".format(
                    level) + bcolors.ENDC)
            exit(1)
        if not force:
            if self.is_connected:
                print(start + color + ' ' + msg + bcolors.ENDC)
        else:
            print(start + color + ' ' + msg + bcolors.ENDC)

    def exec_cmd(self, cmd):
        """
        Run a command on a remote host via ssh (Suitable for Servers)
        :param cmd: Command to run on a remote host
        :return: dict
        """
        if self.is_connected:
            stdin, stdout, stderr = self.ssh.exec_command(cmd)
            self.info['connected'] = self.is_connected
            self.info['cmd'] = cmd
            self.info['stdout'] = stdout.read().decode("utf-8")
            self.info['stderr'] = stderr.read().decode("utf-8")
            self.info['exit_code'] = stdout.channel.recv_exit_status()
            return self.info
        elif not self.is_connected:
            self.info['cmd'] = cmd
            self.info['connected'] = self.is_connected
            self.info['stdout'] = ''
            self.info['stderr'] = ("Failed to connect to %s" % self.host)
            self.info['exit_code'] = ''
            return self.info

    def shell(self, cmd=None, cmd_from_file=None, print_stdout=False, stderr_search_keyword='\^', exit_on_fail=True,
              print_json=False, search=None):
        """
        Method to execute shell commands through SSH shell channel, similar to attaching to a shell session
        :param cmd_from_file: to run commands from a text file
        :param exit_on_fail: fail if STDERR is found
        :param stderr_search_keyword: by default it searches for "^"  to catch stderr on Cisco devices, you can change it as it suits you
        :param print_json: Whether to print JSON to output
        :param cmd: command to be run, make sure the the command ends with a new line, i.e "sh vlan br\n"
        :param print_stdout: to print cmd stdout in terminal with (Blue color)
        :param search: Option to Search the command stdout with Regexp
        :return: dictionary
        """

        if self.is_connected:

            if (cmd_from_file is not None) and (cmd is not None):
                print("[ Error ] " + bcolors.FAIL + "You can only use 'cmd' or 'cmd_from_file' options" + bcolors.ENDC)
                exit(1)

            if cmd_from_file is not None:
                if os.path.exists(cmd_from_file):
                    f = open(cmd_from_file, 'r')
                    cmd = f.read()
                elif not os.path.isfile(cmd_from_file):
                    print(
                        "[ Error ] " + bcolors.FAIL + "You've specified 'cmd_from_file option' but ({}) is NOT a file".format(
                            cmd_from_file) + bcolors.ENDC)
                    exit(1)

            self.channel.send(cmd + '\n' + '\n')
            time.sleep(2)
            self.info['cmd'] = cmd.replace("\r", '').split("\n")
            cmd_original = self.info['cmd']
            self.info['connected'] = self.is_connected
            self.info['stdout'] = self.channel.recv(9999).decode("utf-8")
            stdout_original = self.info['stdout']
            self.info['stderr'] = get_stderr(stdout_original, stderr_search_keyword)['string'].replace("\r", '').split(
                "\n")
            self.info['search'] = search
            self.info['search_found?'] = None
            self.info['search_match'] = None
            stderr_ = [x for x in self.info['stderr'] if x]
            if len(stderr_) > 0:
                self.info['exit_code'] = 1
            else:
                self.info['stderr'] = []
                self.info['exit_code'] = 0
            if search:
                found = re.findall(search, self.info['stdout'])
                if len(found) > 0:
                    self.info['search_match'] = found
                    self.info['search_found?'] = True
                else:
                    self.info['search_found?'] = False

            if print_json:
                self.info['stdout'] = self.info['stdout'].replace("\r", '')
                self.info['stdout'] = self.info['stdout'].split("\n")
                self.info['cmd'] = [x for x in self.info['cmd'] if x]
                formatted_json = json.dumps(self.info, indent=4, sort_keys=True, ensure_ascii=False)
                colorful_json = highlight(formatted_json.encode('utf8'), lexers.JsonLexer(),
                                          formatters.TerminalFormatter())
                print(colorful_json)
                self.info['stdout'] = stdout_original
                self.info['cmd'] = cmd_original
            else:
                self.info['stdout'] = stdout_original

            if print_stdout:
                print(bcolors.OKBLUE + stdout_original + bcolors.ENDC)
            if exit_on_fail:
                if self.info['exit_code'] > 0:
                    print("")
                    print(bcolors.FAIL + "* * * * * * * * * * * * * * * * * * * * * * *" + bcolors.ENDC)
                    print("[ ERROR ] " + bcolors.FAIL + "Found the following Error:" + bcolors.ENDC)
                    print('')
                    err = get_stderr(stdout_original, stderr_search_keyword)['string']
                    # for c in self.info['cmd']:
                    #    print(bcolors.OKBLUE + c + bcolors.ENDC)
                    print('')
                    print(bcolors.FAIL + err + bcolors.ENDC)
                    print(bcolors.FAIL + "* * * * * * * * * * * * * * * * * * * * * * *" + bcolors.ENDC)
                    print("")
                    exit(1)
            return self.info

        elif not self.is_connected:
            self.info['cmd'] = cmd
            self.info['connected'] = self.is_connected
            self.info['stdout'] = ''
            self.info['stderr'] = ("Failed to connect to %s" % self.host)
            self.info['search_found?'] = None
            self.info['search_match'] = None
            self.info['exit_code'] = None
            return self.info

    def close(self):
        """
        Close the ssh session, ssh session is opened at the initialization of the Class
        :return:
        """
        self.ssh.close()
