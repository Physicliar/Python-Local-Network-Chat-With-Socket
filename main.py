import json
import socket
from threading import Thread
from time import sleep
import nmap

ip_address = ""
my_name = ""
port = 12345
ip_dictionary = {}
encoding = "utf-8"


def get_ip():
    global ip_address
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
    finally:
        s.close()


def create_message(message_type, body=""):
    global my_name
    global ip_address
    message = {}
    if my_name == "":
        print("Enter your name: ")
        my_name = input()
    if message_type == "1":
        message = {"name": my_name, "IP": ip_address, "type": message_type}
    elif message_type == "2":
        message = {"name": my_name, "IP": ip_address, "type": message_type}
    elif message_type == "3":
        message = {"name": my_name, "type": message_type, "body": body}
    return json.dumps(message)


def discover_online_devices():
    global ip_dictionary
    global my_name
    ip_dictionary = {}
    if my_name == "":
        print("Enter your name: ")
    my_name = input()
    print("Scanning ports. Please Wait")
    nm = nmap.PortScanner()
    nm.scan(hosts='192.168.1.0/24', arguments='-Pn', ports="12345")
    for host in nm.all_hosts():
        if nm[host]['tcp'][12345]['state'] == "open":
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((host, port))
                s.sendall(create_message("1").encode(encoding=encoding))
    print("Discover is completed!")


def show_online_devices():
    global ip_dictionary
    if len(ip_dictionary) == 0:
        print("There is no active user")
    else:
        print("Active Users:")
        for key in ip_dictionary.keys():
            print(key)


def listen_message():
    global ip_dictionary

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", port))
        s.listen()
        while True:
            conn, address = s.accept()
            with conn:
                output = conn.recv(10240)
                if output == "" or output is None:
                    print("There is a problem about your socket you should restart your cmd or computer")
                    break

                response = json.loads(output.decode(encoding=encoding))
                if response["type"] == "1":
                    if response["IP"] != ip_address:
                        ip_dictionary[response["name"]] = response["IP"]
                    respond_message = create_message("2")
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as new_socket:
                        new_socket.connect((response["IP"], port))
                        new_socket.sendall(respond_message.encode(encoding=encoding))
                elif response["type"] == "2":
                    if response["IP"] != ip_address:
                        ip_dictionary[response["name"]] = response["IP"]
                elif response["type"] == "3":
                    print(response["name"] + ":   " + response["body"])


def application_user_interface():
    global ip_dictionary
    while True:

        user_input = input()
        if user_input == "list":
            show_online_devices()
        elif user_input.split()[0] == "send":
            receiver = user_input.split()[1]
            if receiver in ip_dictionary.keys():
                receiver_ip = ip_dictionary.get(receiver)
                chat_message = " ".join(user_input.split()[2:])
                json_message = create_message("3", body=chat_message)
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1)
                    try:
                        s.connect((receiver_ip, port))
                        s.sendall(json_message.encode(encoding=encoding))
                    except socket.error:
                        print("message cannot be sent! " + receiver + " is offline!")
                        ip_dictionary.pop(receiver)
            else:
                print("No Such Active User!")
        else:
            print("No Valid Command")

        sleep(0.3)


if __name__ == '__main__':
    get_ip()
    print(ip_address)
    discover_online_devices()
    application_ui_thread = Thread(target=application_user_interface)
    listen_thread = Thread(target=listen_message)
    listen_thread.start()
    application_ui_thread.start()
