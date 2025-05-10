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



    VARIABLES = dict()


def handle_disconnected(cmd: str, args: list[str]):
    match cmd:
        case "conn":
            addr = args[0]
            Global.channel = grpc.insecure_channel(addr)
            Global.reflection_db = ProtoReflectionDescriptorDatabase(Global.channel)
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
                Global.VARIABLES[alias] = data
            else:
                print("WRONG!!!")
        case "alias":
            if len(args) == 2:
                alias, json_val = args[0], args[1]
                print(json_val)
                Global.VARIABLES[alias] = json.loads(json_val)
            else:
                print("WRONG!!")
        case "print":
            if len(args) == 0:
                print(json.dumps(Global.VARIABLES, indent=4))
            elif len(args) == 1:
                alias = args[0]
                print(json.dumps(Global.VARIABLES[alias], indent=4))
            else:
                print("WRONG!!!")
        case "invoke":
            if len(args) == 2:
                service_name, method_name = args[0], args[1]
                full_method_name = create_remote_method(service_name, method_name)
                #Global.methods[full_method_name]()
            else:
                print("WRONG!!!")

  
def make_input_iterator(input_class):
    def impl():
        arg = json.loads('{"vec1": {"coeffs" : [1,2,3]},"vec2": {"coeffs" : [1,1,-1]}}')
        yield json_format.ParseDict(input_class(), arg)        
    return impl
    
def my_parse(s: str):
    if s.startswith("$"):
        return Global.VARIABLES[s[1:]]
    
    return json.loads(s)

def create_remote_method(service_name: str, method_name: str):
    service = Global.desc_pool.FindServiceByName(service_name)
    method = service.FindMethodByName(method_name)

    full_method_name = f"/{service_name}/{method_name}"
    cs = method.client_streaming
    ss = method.server_streaming
    print(full_method_name)
    print(f"client streaming: {cs}; server streaming: {ss};")
    if Global.methods.get(full_method_name) is not None:
        print("cached")
    else:
        input_message_class = message_factory.GetMessageClass(method.input_type)
        output_message_class = message_factory.GetMessageClass(method.output_type)
        if not cs and not ss:
            stub_method = Global.channel.unary_unary(
                full_method_name,
                request_serializer=lambda msg: msg.SerializeToString(),
                response_deserializer=lambda resp: output_message_class().FromString(resp))
            #Global.methods[full_method_name] = stub_method
            req = my_parse(input("[unary request]>> "))
            request_message = input_message_class()
            json_format.ParseDict(req, request_message)
            resp = stub_method(request_message)
            print(json_format.MessageToDict(resp))
            def stub_method_with_input():
                req = my_parse(input("[unary request]>> "))
                request_message = input_message_class()
                json_format.ParseDict(req, request_message)
                resp = stub_method(req)
                print(json_format.MessageToDict(resp))
            Global.methods[full_method_name] = stub_method_with_input
        else:
            print("Not implemented!")
    return full_method_name


if __name__ == "__main__":
    
    for inp in input_loop():
        if inp is None or inp == "":
            continue

        cmd, *args = inp.split()
        if Global.state == State.DISCONNECTED:
            handle_disconnected(cmd, args)
        elif Global.state == State.CONNECTED:
            handle_connected(cmd, args)