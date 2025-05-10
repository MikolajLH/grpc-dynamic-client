from enum import Enum
import os
import platform
import json

import grpc
from grpc_reflection.v1alpha.proto_reflection_descriptor_database import ProtoReflectionDescriptorDatabase
from google.protobuf import descriptor_pool, message_factory, json_format


def clrscr():
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')


def input_loop():
    while True:
        try:
            inp = input("[gRPC dyn client]>> ")
        except (KeyboardInterrupt, EOFError):
            return
        if inp == "exit":
            return
        if inp == ":cls:":
            clrscr()
            inp = ""
        yield inp


class State(Enum):
    DISCONNECTED = 1
    CONNECTED = 2
    REMOTECALL = 3


class Global:
    state = State.DISCONNECTED
    channel: None|grpc.Channel = None
    reflection_db: None|ProtoReflectionDescriptorDatabase = None
    desc_pool: None|descriptor_pool.DescriptorPool = None
    services: list[str] = []
    methods = dict()


    arguments_dict = dict()


def handle_disconnected(cmd: str, args: list[str]):
    match cmd:
        case "conn":
            addr = args[0]
            channel = grpc.insecure_channel(addr)
            Global.reflection_db = ProtoReflectionDescriptorDatabase(channel)
            Global.desc_pool = descriptor_pool.DescriptorPool(Global.reflection_db)
            Global.state = State.CONNECTED
            Global.services = list(Global.reflection_db.get_services())
            print("connected")


def print_service_description(service):
    print(service.full_name)
    for method_name, method in service.methods_by_name.items():
        print(f"Method: {method_name}({method.input_type.name}) returns {method.output_type.name}")
        cs = method.client_streaming
        ss = method.server_streaming
        print(f"Client streaming: {cs}; Server streaming: {ss}; ")
        print()

    print()


def handle_connected(cmd: str, args: list[str]):
    match cmd:
        case "list":
            for i, service_name in enumerate(Global.services):
                print(f"[{i}] {service_name}")
        case "info":
            if len(args) == 1:
                index = int(args[0])
                service_name = Global.services[index]
                service = Global.desc_pool.FindServiceByName(service_name)
                print_service_description(service)
            else:
                print("WRONG!!!")
        case "load":
            if len(args) == 2:
                filename, alias = args[0], args[1]
                with open(filename, 'r') as file:
                    data = json.load(file)
                Global.arguments_dict[alias] = data
            else:
                print("WRONG!!!")
        case "alias":
            if len(args) == 2:
                alias, json_val = args[0], args[1]
                Global.arguments_dict[alias] = json.loads(json_val)
            else:
                print("WRONG!!")
        case "print":
            if len(args) == 0:
                print(json.dumps(Global.arguments_dict, indent=4))
            elif len(args) == 1:
                alias = args[0]
                print(json.dumps(Global.arguments_dict[alias], indent=4))
            else:
                print("WRONG!!!")
        case "invoke":
            pass
            



def handle_remotecall(cmd: str, args: list[str]):
    pass


if __name__ == "__main__":
    
    for inp in input_loop():
        if inp is None or inp == "":
            continue

        cmd, *args = inp.split()
        if Global.state == State.DISCONNECTED:
            handle_disconnected(cmd, args)
        elif Global.state == State.CONNECTED:
            handle_connected(cmd, args)
        elif Global.state == State.REMOTECALL:
            handle_remotecall(cmd, args)