import grpc
from grpc_reflection.v1alpha.proto_reflection_descriptor_database import ProtoReflectionDescriptorDatabase
from google.protobuf import descriptor_pool, message_factory, json_format

HARDCODED = {
    "calculator.IntCalculator" : {
        0: {
            "method": "Evaluate",
            "args": [
                {"op": 0, "arg": {"value": 42 } },
                {"op": 4, "arg": {"value": 9 } },
                {"op": 3, "arg": {"value": 0} },
            ]
        }, 
        1: {
            "method": "ApplyBinOp",
            "args": {
                "op": 0,
                "arg1" : {"value": 13},
                "arg2" : {"value": 27},
            }
        },
        2: {
            "method": "FindPrimes",
            "args": {
                "lb": {"value": 10 },
                "ub": {"value": 30 },
            }
        },
    },
    "calculator.VectorCalculator": {
        0: {
            "method": "AccumulateVec",
            "args": {
                "vec": {"coeffs" : [1,2,3,4,5]},
                "op": 3
            }
        },
        1: {
            "method": "MapVec",
            "args": {
                "vec": {"coeffs" : [1,2,3,4,5]},
                "op": 3
            }
        },
        2: {
            "method": "Dot",
            "args": [
                {
                    "vec1": {"coeffs" : [1,2,3]},
                    "vec2": {"coeffs" : [1,1,-1]}
                },
                {
                    "vec1": {"coeffs" : [2,2,3]},
                    "vec2": {"coeffs" : [1,1,-1]}
                }
                ]
        }
    }
}



def print_service_description(service):
    print(service.full_name)
    for method_name, method in service.methods_by_name.items():
        print(f"Method: {method_name}({method.input_type.name}) returns {method.output_type.name}")
        cs = method.client_streaming
        ss = method.server_streaming
        print(f"Client streaming: {cs}; Server streaming: {ss}; ")
        print()

    print()


def main():
    # 1. Connect to server
    channel = grpc.insecure_channel('127.0.0.1:50051')
    reflection_db = ProtoReflectionDescriptorDatabase(channel)
    desc_pool = descriptor_pool.DescriptorPool(reflection_db)

    print("Available services:")
    services = list(reflection_db.get_services())
    for i, service_name in enumerate(services):
        print(i, service_name)
    service_index = -1
    while service_index not in range(len(services)):
        try:
            service_index = int(input(f"Chose service by providing its index: "))
        except ValueError:
            service_index = -1
    print()
    service_name = services[service_index]
    service = desc_pool.FindServiceByName(service_name)
    print_service_description(service)

    req = None
    while req is None:
        keys = list(HARDCODED[service_name].keys())
        try:
            key = int(input(f"Chose hardcoded request from {keys}: "))
            if key in HARDCODED[service_name].keys():
                req = HARDCODED[service_name][key]
                print(req)
                conf = input("Proceed? (y/n): ")
                if conf != "y":
                    req = None
        except Exception:
            req = None

    method_name = req["method"]

    method = service.FindMethodByName(method_name)
    input_message_class = message_factory.GetMessageClass(method.input_type)
    output_message_class = message_factory.GetMessageClass(method.output_type)

    
    full_method_name = f"/{service_name}/{method_name}"
    print(f"creating and calling stub for {full_method_name}")

    cs = method.client_streaming
    ss = method.server_streaming
    if not cs and not ss:
        request_message = input_message_class()
        json_format.ParseDict(req["args"], request_message)

        stub_method = channel.unary_unary(
            full_method_name, 
            request_serializer=lambda msg: msg.SerializeToString(),
            response_deserializer=lambda resp: output_message_class().FromString(resp))
        
        resp = stub_method(request_message)
        print("Response:", json_format.MessageToDict(resp))

    elif cs and not ss:
        stub_method = None
    elif not cs and ss:
        request_message = input_message_class()
        json_format.ParseDict(req["args"], request_message)

        stub_method = channel.unary_stream(
            full_method_name,
            request_serializer=lambda msg: msg.SerializeToString(),
            response_deserializer=lambda resp: output_message_class().FromString(resp))
        resp_iter = stub_method(request_message)
        try:
            for resp in resp_iter:
                print(json_format.MessageToDict(resp))
        except Exception as e:
            print(e)
    elif cs and ss:
        def request_iterator():
            for rd in req["args"]:
                rm = input_message_class()
                json_format.ParseDict(rd, rm)
                yield rm
        resp_iter = channel.stream_stream(
            full_method_name,
            request_serializer=lambda msg: msg.SerializeToString(),
            response_deserializer=lambda resp: output_message_class().FromString(resp)
            )(request_iterator())
        try:
            for resp in resp_iter:
                print(json_format.MessageToDict(resp))
        except Exception as e:
            print(e)


        

if __name__ == "__main__":
    main()
