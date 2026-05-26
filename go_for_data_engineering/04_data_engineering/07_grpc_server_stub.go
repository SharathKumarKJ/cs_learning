// gRPC server stub.
// Requires protoc-generated code from a .proto file.
// go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
// go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest
package main

import (
	"context"
	"log"
	"net"

	"google.golang.org/grpc"
	// pb "example.com/orders/proto" // generated package
)

// Hypothetical generated interface:
// type OrderServiceServer interface {
//     GetOrder(context.Context, *GetOrderRequest) (*Order, error)
// }

type server struct {
	// pb.UnimplementedOrderServiceServer
}

// func (s *server) GetOrder(ctx context.Context, req *pb.GetOrderRequest) (*pb.Order, error) {
//     return &pb.Order{Id: req.Id, Status: "OPEN"}, nil
// }

func main() {
	lis, err := net.Listen("tcp", ":50051")
	if err != nil {
		log.Fatal(err)
	}
	grpcServer := grpc.NewServer()
	// pb.RegisterOrderServiceServer(grpcServer, &server{})
	log.Println("grpc listening on :50051")
	_ = grpcServer.Serve(lis)
	_ = context.Background()
}
