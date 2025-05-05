package main

import (
	"context"
	"log"
	"net"

	pb "grpc-server/gen"

	"google.golang.org/grpc"
	"google.golang.org/grpc/reflection"
)

type server struct {
	pb.UnimplementedCalculatorServer
}

func (s *server) Add(ctx context.Context, args *pb.BinaryOpArguments) (*pb.BinaryOpResult, error) {
	arg1 := args.GetArg1()
	arg2 := args.GetArg2()
	res := arg1 + arg2
	log.Printf("Received arguments: %d + %d = %d", arg1, arg2, res)
	return &pb.BinaryOpResult{Res: res}, nil
}

func main() {
	lis, err := net.Listen("tcp", ":50051")
	if err != nil {
		log.Fatalf("Failed to listen: %v", err)
	}
	s := grpc.NewServer()

	// Register service and reflection for dynamic clients like grpcurl
	pb.RegisterCalculatorServer(s, &server{})
	reflection.Register(s)

	log.Println("Server is running on :50051")
	if err := s.Serve(lis); err != nil {
		log.Fatalf("Failed to serve: %v", err)
	}
}
