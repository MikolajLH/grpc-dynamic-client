package main

import (
	"context"
	"io"
	"log"
	"math"
	"net"
	"time"

	pb "grpc-server/gen"

	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/reflection"
	"google.golang.org/grpc/status"
)

type intserver struct {
	pb.UnimplementedIntCalculatorServer
}

type Int = int32

var IntOperations = map[pb.BinaryIntOp]func(Int, Int) Int{
	pb.BinaryIntOp_ADDI: func(a, b Int) Int { return a + b },
	pb.BinaryIntOp_SUBI: func(a, b Int) Int { return a - b },
	pb.BinaryIntOp_MULI: func(a, b Int) Int { return a * b },
	pb.BinaryIntOp_MODI: func(a, b Int) Int { return a % b },
	pb.BinaryIntOp_DIVI: func(a, b Int) Int { return a / b },
}

func (s *intserver) ApplyBinOp(ctx context.Context, arg *pb.ApplyBinOpArg) (*pb.Int, error) {

	op := arg.GetOp()
	arg1 := arg.GetArg1().GetValue()
	arg2 := arg.GetArg2().GetValue()
	if op == pb.BinaryIntOp_DIVI && arg2 == 0 {
		return nil, status.Error(codes.InvalidArgument, "Can't divide by zero")
	}

	res := IntOperations[op](arg1, arg2)

	log.Printf("operation: %s; arg1: %d; arg2: %d; result: %d", op, arg1, arg2, res)
	return &pb.Int{Value: res}, nil
}

func (s *intserver) Evaluate(stream pb.IntCalculator_EvaluateServer) error {
	var res Int = 0
	for {
		req, err := stream.Recv()
		// End of stream
		if err == io.EOF {
			return nil
		}
		if err != nil {
			return err
		}
		op := req.GetOp()
		arg := req.GetArg().GetValue()
		if op == pb.BinaryIntOp_DIVI && arg == 0 {
			return status.Error(codes.InvalidArgument, "Can't divide by zero")
		}
		res = IntOperations[op](res, arg)
		log.Printf("operation: %s; arg: %d; result: %d", op, arg, res)
		if err := stream.Send(&pb.Int{Value: res}); err != nil {
			return err
		}
		time.Sleep(500 * time.Millisecond)
	}
}

func (s *intserver) FindPrimes(arg *pb.FindPrimesArg, stream pb.IntCalculator_FindPrimesServer) error {
	lb := arg.GetLb().GetValue()
	ub := arg.GetUb().GetValue()

	if lb < 0 || ub < 0 || lb >= ub {
		return status.Error(codes.InvalidArgument, "Invalid upper bound and lower bound")
	}

	isPrime := func(n Int) bool {
		if n < 2 {
			return false
		}
		for i := Int(2); i*i <= n; i++ {
			if n%i == 0 {
				return false
			}
		}
		return true
	}

	for i := lb; i < ub; i++ {
		if isPrime(i) {
			if err := stream.Send(&pb.Int{Value: i}); err != nil {
				return err
			}
		}
		time.Sleep(500 * time.Millisecond)
	}
	return nil
}

///

type vecserver struct {
	pb.UnimplementedVectorCalculatorServer
}

func (s *vecserver) AccumulateVec(ctx context.Context, arg *pb.AccumulateVecArg) (*pb.Float, error) {
	var AccOperations = map[pb.AccumulateVecOp]func(float64, float64) float64{
		pb.AccumulateVecOp_MIN: func(a, b float64) float64 { return min(a, b) },
		pb.AccumulateVecOp_MAX: func(a, b float64) float64 { return max(a, b) },
		pb.AccumulateVecOp_ADD: func(a, b float64) float64 { return a + b },
		pb.AccumulateVecOp_MUL: func(a, b float64) float64 { return a * b },
	}
	coeffs := arg.GetVec().GetCoeffs()
	op := AccOperations[arg.GetOp()]

	if len(coeffs) == 0 {
		return nil, status.Error(codes.InvalidArgument, "Empty vector")
	}

	res := coeffs[0]
	for _, num := range coeffs[1:] {
		res = op(res, num)
	}
	log.Printf("method: AccumulateVec; operation: %s; result: %f", arg.GetOp(), res)
	return &pb.Float{Value: res}, nil
}

func (s *vecserver) MapVec(ctx context.Context, arg *pb.MapVecArg) (*pb.FloatVector, error) {
	var MapOperations = map[pb.MapVecOp]func(float64) float64{
		pb.MapVecOp_ID:     func(x float64) float64 { return x },
		pb.MapVecOp_SIN:    func(x float64) float64 { return math.Sin(x) },
		pb.MapVecOp_COS:    func(x float64) float64 { return math.Cos(x) },
		pb.MapVecOp_SQUARE: func(x float64) float64 { return x * x },
		pb.MapVecOp_SQRT:   func(x float64) float64 { return math.Sqrt(x) },
	}
	coeffs := arg.GetVec().GetCoeffs()
	opName := arg.GetOp()
	op := MapOperations[opName]
	if opName == pb.MapVecOp_SQRT {
		for x := range coeffs {
			if x < 0 {
				return nil, status.Error(codes.InvalidArgument, "Sqrt on negative number")
			}
		}
	}
	if len(coeffs) == 0 {
		return nil, status.Error(codes.InvalidArgument, "Empty vector")
	}

	for i, x := range coeffs {
		coeffs[i] = op(x)
	}
	log.Printf("method: MapVec; operation: %s", arg.GetOp())
	return &pb.FloatVector{Coeffs: coeffs}, nil
}

func (s *vecserver) Dot(stream pb.VectorCalculator_DotServer) error {
	for {
		req, err := stream.Recv()
		if err == io.EOF {
			return nil
		}
		if err != nil {
			return err
		}
		coeffs1 := req.GetVec1().GetCoeffs()
		coeffs2 := req.GetVec2().GetCoeffs()

		if len(coeffs1) != len(coeffs2) || len(coeffs1) == 0 {
			return status.Error(codes.InvalidArgument, "Invalid vectors")
		}

		res := float64(0)
		for i := 0; i < len(coeffs1); i++ {
			res += coeffs1[i] * coeffs2[i]
		}
		if err := stream.Send(&pb.Float{Value: res}); err != nil {
			return err
		}
	}
}

func main() {
	lis, err := net.Listen("tcp", ":50051")
	if err != nil {
		log.Fatalf("Failed to listen: %v", err)
	}
	s := grpc.NewServer()
	pb.RegisterIntCalculatorServer(s, &intserver{})
	pb.RegisterVectorCalculatorServer(s, &vecserver{})

	reflection.Register(s)

	log.Println("Server is running on :50051")
	if err := s.Serve(lis); err != nil {
		log.Fatalf("Failed to serve: %v", err)
	}
}
