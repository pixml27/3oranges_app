import select
import socket
import pickle
import csv
import pandas as pd

SERVER_ADDRESS = ('192.168.1.50', 8686)
MAX_CONNECTIONS = 10
INPUTS = list()
OUTPUTS = list()
path_to_departments = "log\\departments.txt"


def get_departments(path_departments):
    with open(path_departments, encoding='utf-8') as file:
        departments = [row.strip() for row in file]
    i = 0
    size = len(departments)
    while i < size:
        if departments[i] == '':
            departments.remove(departments[i])
            i -= 1
            size = len(departments)
        else:
            i += 1
    print(departments)
    return departments


def break_error():
    None


def send_departaments(res):
    departs = get_departments(path_to_departments)
    print(departs)
    departments = pickle.dumps(departs)
    res.send(departments)


def send_data(res):
    df = pd.read_csv('data.csv', encoding='utf-8')
    a = pickle.dumps(df)
    res.send(a)


def save_data(data_to_save):
    data_to_save = data_to_save[1:3]+data_to_save[4] + [data_to_save[0]]+[data_to_save[-1]]+[data_to_save[-3]]
    with open('data.csv', "a", newline="", encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(data_to_save)
        file.close()


def save_departaments(departaments_to_save):
    all_dep = departaments_to_save[0]
    for depart in departaments_to_save[1:]:
        all_dep += '\n'
        all_dep += depart
    file = open(path_to_departments, "w", encoding='utf-8')
    file.write(all_dep)
    file.close()


def what_to_do(data_from_connection, resr):
    if type(data_from_connection) == str:      
        if data_from_connection == 'get_departments':
            send_departaments(resr)
        elif data_from_connection == 'get_data':
            send_data(resr)
        else:
            break_error()
    elif type(data_from_connection) == list:
        if data_from_connection[0] == 'worker':
            save_data(data_from_connection[1:])
        elif data_from_connection[0] == 'hr':
            save_departaments(data_from_connection[1:])
        else:
            break_error()
    else:
        break_error()


def get_non_blocking_server_socket():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setblocking(0)
    server.bind(SERVER_ADDRESS)
    server.listen(MAX_CONNECTIONS)

    return server


def handle_readables(readables, server):
    for resource in readables:

        if resource is server:
            connection, client_address = resource.accept()
            connection.setblocking(0)
            INPUTS.append(connection)
            print("new connection from {address}".format(address=client_address))

        else:
            data = ""
            try:
                data = resource.recv(1024)

            except ConnectionResetError:
                pass

            if data:

                received_data = pickle.loads(data)
                print(received_data)
                what_to_do(received_data, resource)

                if resource not in OUTPUTS:
                    OUTPUTS.append(resource)

            else:

                clear_resource(resource)


def clear_resource(resource):
    if resource in OUTPUTS:
        OUTPUTS.remove(resource)
    if resource in INPUTS:
        INPUTS.remove(resource)
    resource.close()


def handle_writables(writables):
    for resource in writables:
        try:
            resource.send(bytes('Hello from server!', encoding='UTF-8'))
        except OSError:
            clear_resource(resource)


if __name__ == '__main__':

    server_socket = get_non_blocking_server_socket()
    INPUTS.append(server_socket)

    print("server is running, please, press ctrl+c to stop")
    try:
        while INPUTS:
            readables, writables, exceptional = select.select(INPUTS, OUTPUTS, INPUTS)
            handle_readables(readables, server_socket)
            # handle_writables(writables)
    except KeyboardInterrupt:
        clear_resource(server_socket)
        print("Server stopped! Thank you for using!")
