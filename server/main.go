package main

import (
	"log"
	"net"

	"grpc-server/calculator"
	pb "grpc-server/gen"

	"google.golang.org/grpc"
	"google.golang.org/grpc/reflection"
)

func main() {
	lis, err := net.Listen("tcp", ":50051")
	if err != nil {
		log.Fatalf("Failed to listen: %v", err)
	}

	s := grpc.NewServer()
	pb.RegisterIntCalculatorServer(s, &calculator.IntCalculatorServer{})
	pb.RegisterVectorCalculatorServer(s, &calculator.VectorCalculatorServer{})

	reflection.Register(s)

	log.Println("Server is running on :50051")
	if err := s.Serve(lis); err != nil {
		log.Fatalf("Failed to serve: %v", err)
	}
}
