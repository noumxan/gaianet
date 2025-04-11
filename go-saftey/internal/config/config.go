package config

import (
	"os"

	"github.com/joho/godotenv"
)

type Config struct {
	InstagramAccessToken string
	OpenAIAPIKey         string
	ServerPort           string
}

func LoadConfig() (*Config, error) {
	if err := godotenv.Load(); err != nil {
		return nil, err
	}

	return &Config{
		InstagramAccessToken: getEnv("INSTAGRAM_ACCESS_TOKEN", ""),
		OpenAIAPIKey:         getEnv("OPENAI_API_KEY", ""),
		ServerPort:           getEnv("SERVER_PORT", "8080"),
	}, nil
}

func getEnv(key, defaultValue string) string {
	if value, exists := os.LookupEnv(key); exists {
		return value
	}
	return defaultValue
}
