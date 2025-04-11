package server

import (
	"net/http"

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
}

func NewServer(cfg *config.Config) *Server {
	s := &Server{
		router:    gin.Default(),
		config:    cfg,
		instagram: instagram.NewClient(cfg.InstagramAccessToken),
		openai:    openai.NewClient(cfg.OpenAIAPIKey),
	}

	s.setupRoutes()
	return s
}

func (s *Server) setupRoutes() {
	s.router.GET("/health", s.healthCheck)
	s.router.GET("/messages", s.getMessages)
	s.router.POST("/analyze", s.analyzeContent)
}

func (s *Server) healthCheck(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status": "healthy",
	})
}

func (s *Server) getMessages(c *gin.Context) {
	messages, err := s.instagram.GetRecentDMs(c.Request.Context())
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, messages)
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
	return s.router.Run(":" + s.config.ServerPort)
}
