package calculator

import (
	"context"
	"io"
	"log"
	"time"

	pb "grpc-server/gen"

	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

type IntCalculatorServer struct {
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

func (s *IntCalculatorServer) ApplyBinOp(ctx context.Context, arg *pb.ApplyBinOpArg) (*pb.Int, error) {

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

func (s *IntCalculatorServer) Evaluate(stream pb.IntCalculator_EvaluateServer) error {
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

func (s *IntCalculatorServer) FindPrimes(arg *pb.FindPrimesArg, stream pb.IntCalculator_FindPrimesServer) error {
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
