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

if __name__ == "__main__":
    for inp in input_loop():
        if inp is None or inp == "":
            continue