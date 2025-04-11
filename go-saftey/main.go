package main

import (
	"log"

	"github.com/gaianet/go-safety/internal/config"
	"github.com/gaianet/go-safety/internal/server"
)

func main() {
	cfg, err := config.LoadConfig()
	if err != nil {
		log.Fatalf("Failed to load configuration: %v", err)
	}

	srv := server.NewServer(cfg)
	log.Printf("Starting server on port %s", cfg.ServerPort)
	if err := srv.Start(); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}
