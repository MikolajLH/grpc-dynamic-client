from enum import Enum
import os
import platform
import json
import re
import threading

import grpc
from grpc_reflection.v1alpha.proto_reflection_descriptor_database import ProtoReflectionDescriptorDatabase
from google.protobuf import descriptor_pool, message_factory, json_format


class Global:
    channel: None|grpc.Channel = None
    reflection_db: None|ProtoReflectionDescriptorDatabase = None
    desc_pool: None|descriptor_pool.DescriptorPool = None
    services: list[str] = []

    VARIABLES = dict()

def clrscr():
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')

def print_service_description(service):
    print(service.full_name)
    for method_name, method in service.methods_by_name.items():
        print(f"Method: {method_name}({method.input_type.name}) returns {method.output_type.name}")
        cs = method.client_streaming
        ss = method.server_streaming
        print(f"Client streaming: {cs}; Server streaming: {ss}; ")
        print()

    print()


def call_remote_method(service_name: str, method_name: str):
    service = Global.desc_pool.FindServiceByName(service_name)
    method = service.FindMethodByName(method_name)

    def handle_response_stream(resp_iter):
        try:
            for resp in resp_iter:
                print(json_format.MessageToDict(resp))
        except Exception as e:
            print("Exception:", e)

    def handle_request_stream(message_class):
        while True:
            inp = parse(input("[request]>> "))
            if inp == "!":
                
                return
            try:
                req = json.loads(inp)
                rm = message_class()
                json_format.ParseDict(req, rm)
                yield rm
            except Exception as e:
                print("Exception:", e)
                return
            

    full_method_name = f"/{service_name}/{method_name}"
    cs = method.client_streaming
    ss = method.server_streaming
    print(full_method_name)
    print(f"client streaming: {cs}; server streaming: {ss};")
    input_message_class = message_factory.GetMessageClass(method.input_type)
    output_message_class = message_factory.GetMessageClass(method.output_type)
    if not cs and not ss:
        req = json.loads(parse(input("[(1 -> 1) request]>> ")))
        request_message = input_message_class()
        json_format.ParseDict(req, request_message)
        stub_method = Global.channel.unary_unary(
            full_method_name,
            request_serializer=lambda msg: msg.SerializeToString(),
            response_deserializer=lambda resp: output_message_class().FromString(resp))
        resp = stub_method(request_message)
        print(json_format.MessageToDict(resp))

    elif not cs and ss:
        req = json.loads(parse(input("[(1 -> *) request]>> ")))
        request_message = input_message_class()
        json_format.ParseDict(req, request_message)
        stub_method = Global.channel.unary_stream(
            full_method_name,
            request_serializer=lambda msg: msg.SerializeToString(),
            response_deserializer=lambda resp: output_message_class().FromString(resp))
        
        resp_iter = stub_method(request_message)
        thread = threading.Thread(target=handle_response_stream, args=[resp_iter])
        thread.start()
        thread.join()

    elif cs and not ss:
        stub_method = Global.channel.stream_unary(
            full_method_name,
            request_serializer=lambda msg: msg.SerializeToString(),
            response_deserializer=lambda resp: output_message_class().FromString(resp))
        
        resp = stub_method(handle_request_stream(input_message_class))
        print(json_format.MessageToDict(resp))
    else:
        stub_method = Global.channel.stream_stream(
            full_method_name,
            request_serializer=lambda msg: msg.SerializeToString(),
            response_deserializer=lambda resp: output_message_class().FromString(resp))
        
        resp_iter = stub_method(handle_request_stream(input_message_class))
        thread = threading.Thread(target=handle_response_stream, args=[resp_iter])
        thread.start()
        thread.join()

    
def parse(text: str) -> str:
    parts = re.split(r'(\s+)', text)
    processed_parts = []
    for part in parts:
        new_part = part
        if part.startswith("$"):
            if part[1:] in Global.VARIABLES:
                new_part = json.dumps(Global.VARIABLES[part[1:]])
            else:
                print(f"Warning: There is no saved variable with the name {part}")
        processed_parts.append(new_part)
    
    return "".join(processed_parts)


def input_loop():
    while True:
        try:
            inp = parse(input("[gRPC dyn client]>> "))
            print("<<", inp)                
        except (KeyboardInterrupt, EOFError):
            return
        if inp == "exit":
            return
        if inp == ":cls:":
            clrscr()
            inp = ""
        yield inp


def handle_command(cmd: str, args: list[str]):
    match cmd:
        case "conn":
            addr = args[0]
            if Global.channel is None:
                Global.channel = grpc.insecure_channel(addr)
                Global.reflection_db = ProtoReflectionDescriptorDatabase(Global.channel)
                Global.desc_pool = descriptor_pool.DescriptorPool(Global.reflection_db)
                Global.services = list(Global.reflection_db.get_services())
                print("connected")
            else:
                print("Already connected, disconnect first")
            
        case "disc":
            if Global.channel is not None:
                Global.channel = None
                Global.reflection_db = None
                Global.desc_pool = None
                Global.services = []
                print("disconnected")
            else:
                print("can't disconnect if not connected")

        case "list":
            for i, service_name in enumerate(Global.services):
                print(f"[{i}] {service_name}")

        case "info":
            index = int(args[0])
            service_name = Global.services[index]
            service = Global.desc_pool.FindServiceByName(service_name)
            print_service_description(service)
        case "var":
            var_name, json_val = args[0], args[1:]
            Global.VARIABLES[var_name] = json.loads("".join(json_val))
        case "loadto":
            filename, alias = args[0], args[1]
            with open(filename, 'r') as file:
                data = json.load(file)
                Global.VARIABLES[alias] = data
        case "call":
            service_name = args[0]
            method_name = args[1]
            call_remote_method(service_name, method_name)


if __name__ == "__main__":
    for inp in input_loop():
        if inp is None or inp == "":
            continue
        cmd, *args = inp.split()
        handle_command(cmd, args)