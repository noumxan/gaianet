package config

import (
	"fmt"
	"log"
	"os"
	"strconv"

	"github.com/joho/godotenv"
)

type Config struct {
	InstagramAccessToken string
	OpenAIAPIKey         string
	ServerPort           string
	Debug                bool
}

func LoadConfig() (*Config, error) {
	if err := godotenv.Load(); err != nil {
		log.Printf("Warning: .env file not found or could not be loaded: %v", err)
		// Continue with environment variables that might be set elsewhere
	}

	config := &Config{
		InstagramAccessToken: getEnv("INSTAGRAM_ACCESS_TOKEN", ""),
		OpenAIAPIKey:         getEnv("OPENAI_API_KEY", ""),
		ServerPort:           getEnv("SERVER_PORT", "8080"),
		Debug:                getBoolEnv("DEBUG", false),
	}

	// Validate required configuration
	if err := config.Validate(); err != nil {
		return nil, err
	}

	// Print configuration (with sensitive parts redacted)
	config.LogConfig()

	return config, nil
}

func (c *Config) Validate() error {
	if c.InstagramAccessToken == "" {
		return fmt.Errorf("INSTAGRAM_ACCESS_TOKEN is required")
	}

	if c.OpenAIAPIKey == "" {
		return fmt.Errorf("OPENAI_API_KEY is required")
	}

	return nil
}

func (c *Config) LogConfig() {
	log.Println("Configuration loaded with the following settings:")
	log.Printf("- SERVER_PORT: %s", c.ServerPort)
	log.Printf("- DEBUG: %v", c.Debug)

	// Redact sensitive information
	igTokenRedacted := redactToken(c.InstagramAccessToken)
	openaiKeyRedacted := redactToken(c.OpenAIAPIKey)

	log.Printf("- INSTAGRAM_ACCESS_TOKEN: %s", igTokenRedacted)
	log.Printf("- OPENAI_API_KEY: %s", openaiKeyRedacted)
}

func redactToken(token string) string {
	if len(token) <= 8 {
		return "******"
	}
	return token[:4] + "..." + token[len(token)-4:]
}

func getEnv(key, defaultValue string) string {
	if value, exists := os.LookupEnv(key); exists {
		return value
	}
	return defaultValue
}

func getBoolEnv(key string, defaultValue bool) bool {
	if value, exists := os.LookupEnv(key); exists {
		b, err := strconv.ParseBool(value)
		if err != nil {
			log.Printf("Warning: Could not parse %s as boolean: %v. Using default: %v", key, err, defaultValue)
			return defaultValue
		}
		return b
	}
	return defaultValue
}
