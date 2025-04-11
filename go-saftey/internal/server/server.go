package server

import (
	"context"
	"log"
	"net/http"
	"sync"
	"time"

	"github.com/gaianet/go-safety/internal/config"
	"github.com/gaianet/go-safety/internal/instagram"
	"github.com/gaianet/go-safety/internal/openai"
	"github.com/gin-gonic/gin"
)

type Server struct {
	router    *gin.Engine
	config    *config.Config
	instagram *instagram.Client
	openai    *openai.Client
	mu        sync.RWMutex
	messages  []instagram.Message
}

func NewServer(cfg *config.Config) *Server {
	s := &Server{
		router:    gin.Default(),
		config:    cfg,
		instagram: instagram.NewClient(cfg.InstagramAccessToken),
		openai:    openai.NewClient(cfg.OpenAIAPIKey),
		messages:  make([]instagram.Message, 0),
	}

	s.setupRoutes()
	return s
}

func (s *Server) setupRoutes() {
	s.router.GET("/health", s.healthCheck)
	s.router.GET("/messages", s.getMessages)
	s.router.POST("/analyze", s.analyzeContent)
	s.router.POST("/force-check", s.forceCheckMessages)
}

func (s *Server) healthCheck(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status": "healthy",
	})
}

func (s *Server) getMessages(c *gin.Context) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	// If no messages are cached, try to fetch them immediately
	if len(s.messages) == 0 {
		s.mu.RUnlock() // Unlock before potentially long operation
		s.checkMessages()
		s.mu.RLock() // Lock again for reading
	}

	c.JSON(http.StatusOK, gin.H{
		"messages": s.messages,
		"count":    len(s.messages),
		"status":   "success",
	})
}

func (s *Server) forceCheckMessages(c *gin.Context) {
	log.Println("Force checking messages...")
	s.checkMessages()

	s.mu.RLock()
	defer s.mu.RUnlock()

	c.JSON(http.StatusOK, gin.H{
		"messages": s.messages,
		"count":    len(s.messages),
		"status":   "success",
	})
}

func (s *Server) analyzeContent(c *gin.Context) {
	var request struct {
		Content string `json:"content"`
	}

	if err := c.ShouldBindJSON(&request); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "Invalid request body",
		})
		return
	}

	analysis, err := s.openai.AnalyzeContent(c.Request.Context(), request.Content)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, analysis)
}

func (s *Server) Start() error {
	// Start the background worker
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	go s.messageWorker(ctx)

	// Start the HTTP server
	log.Printf("Server starting on port %s", s.config.ServerPort)
	return s.router.Run(":" + s.config.ServerPort)
}

func (s *Server) messageWorker(ctx context.Context) {
	ticker := time.NewTicker(3 * time.Second)
	defer ticker.Stop()

	// Do an initial check at startup
	s.checkMessages()

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			s.checkMessages()
		}
	}
}

func (s *Server) checkMessages() {
	log.Println("Checking for new Instagram messages...")

	// First try the primary method
	messages, err := s.instagram.GetRecentDMs(context.Background())
	if err != nil {
		log.Printf("Error fetching messages with primary method: %v", err)

		// If primary method fails, try the alternative
		alternativeMessages, altErr := s.instagram.GetRecentDMsAlternative(context.Background())
		if altErr != nil {
			log.Printf("Error fetching messages with alternative method: %v", altErr)
			return
		}

		messages = alternativeMessages
	}

	// If we got no messages but no error, log it
	if len(messages) == 0 {
		log.Println("No messages found in response")
	} else {
		log.Printf("Successfully fetched %d messages", len(messages))

		// Process new messages
		for _, msg := range messages {
			if msg.MediaURL != "" {
				log.Printf("Processing media from message %s", msg.ID)
				// Here you could download and analyze the media
			}
		}
	}

	s.mu.Lock()
	s.messages = messages
	s.mu.Unlock()
}
