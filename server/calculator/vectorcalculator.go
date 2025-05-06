package calculator

import (
	"context"
	"io"
	"log"
	"math"

	pb "grpc-server/gen"

	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

type VectorCalculatorServer struct {
	pb.UnimplementedVectorCalculatorServer
}

func (s *VectorCalculatorServer) AccumulateVec(ctx context.Context, arg *pb.AccumulateVecArg) (*pb.Float, error) {
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

func (s *VectorCalculatorServer) MapVec(ctx context.Context, arg *pb.MapVecArg) (*pb.FloatVector, error) {
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

func (s *VectorCalculatorServer) Dot(stream pb.VectorCalculator_DotServer) error {
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
