from enum import Enum
import os
import platform
import json

import grpc
from grpc_reflection.v1alpha.proto_reflection_descriptor_database import ProtoReflectionDescriptorDatabase
from google.protobuf import descriptor_pool, message_factory, json_format


class Global:
    channel: None|grpc.Channel = None
    reflection_db: None|ProtoReflectionDescriptorDatabase = None
    desc_pool: None|descriptor_pool.DescriptorPool = None
    services: list[str] = []
    methods = dict()

    VARIABLES = dict()

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
            pass
        case "info":
            pass
        case "alias":
            pass
        case "load":
            pass
        case "print":
            pass
        case "invoke":
            pass


if __name__ == "__main__":
    for inp in input_loop():
        if inp is None or inp == "":
            continue
        
        cmd, *args = inp.split()
        handle_command(cmd, args)