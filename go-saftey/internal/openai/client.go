package openai

import (
	"context"
	"fmt"

	"github.com/sashabaranov/go-openai"
)

type Client struct {
	client *openai.Client
}

func NewClient(apiKey string) *Client {
	return &Client{
		client: openai.NewClient(apiKey),
	}
}

type ContentAnalysis struct {
	IsHarmful     bool
	IsChildSafe   bool
	IsAppropriate bool
	Reasoning     string
}

func (c *Client) AnalyzeContent(ctx context.Context, content string) (*ContentAnalysis, error) {
	prompt := fmt.Sprintf(`Analyze the following content and determine if it is:
1. Harmful or dangerous
2. Suitable for children
3. Generally appropriate

Content: %s

Please provide a detailed analysis and reasoning for each category.`, content)

	resp, err := c.client.CreateChatCompletion(
		ctx,
		openai.ChatCompletionRequest{
			Model: openai.GPT4,
			Messages: []openai.ChatCompletionMessage{
				{
					Role:    openai.ChatMessageRoleSystem,
					Content: "You are a content moderation assistant. Analyze the content and provide clear, objective assessments.",
				},
				{
					Role:    openai.ChatMessageRoleUser,
					Content: prompt,
				},
			},
		},
	)
	if err != nil {
		return nil, err
	}

	// Parse the response and create ContentAnalysis
	// This is a simplified version - in a real implementation, you'd want to parse the response more carefully
	analysis := &ContentAnalysis{
		Reasoning: resp.Choices[0].Message.Content,
	}

	// Here you would implement logic to parse the response and set the boolean flags
	// based on the AI's analysis. This is a placeholder implementation.
	analysis.IsHarmful = false
	analysis.IsChildSafe = true
	analysis.IsAppropriate = true

	return analysis, nil
}
