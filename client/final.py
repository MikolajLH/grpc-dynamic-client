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


def handle_command(cmd: str, args: list[str]):
    match cmd:
        case "conn":
            pass
        case "close":
            pass
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