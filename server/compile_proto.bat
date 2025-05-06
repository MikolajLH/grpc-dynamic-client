@echo off
protoc --go_out=. --go-grpc_out=. .\calculator.proto