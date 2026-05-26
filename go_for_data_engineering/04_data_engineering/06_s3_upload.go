// Upload a file to S3 using AWS SDK v2.
// go get github.com/aws/aws-sdk-go-v2/config github.com/aws/aws-sdk-go-v2/service/s3
package main

import (
	"context"
	"fmt"
	"log"
	"os"

	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/s3"
)

func main() {
	ctx := context.Background()
	cfg, err := config.LoadDefaultConfig(ctx)
	if err != nil {
		log.Fatal(err)
	}
	client := s3.NewFromConfig(cfg)

	f, err := os.Open("data.csv")
	if err != nil {
		log.Fatal(err)
	}
	defer f.Close()

	_, err = client.PutObject(ctx, &s3.PutObjectInput{
		Bucket: stringPtr("my-bucket"),
		Key:    stringPtr("uploads/data.csv"),
		Body:   f,
	})
	if err != nil {
		log.Fatal(err)
	}
	fmt.Println("uploaded")
}

func stringPtr(s string) *string { return &s }
