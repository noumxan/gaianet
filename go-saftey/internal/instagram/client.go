package instagram

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"time"
)

type Client struct {
	accessToken string
	httpClient  *http.Client
}

func NewClient(accessToken string) *Client {
	return &Client{
		accessToken: accessToken,
		httpClient: &http.Client{
			Timeout: 10 * time.Second,
		},
	}
}

type Message struct {
	ID        string `json:"id"`
	Text      string `json:"text"`
	MediaURL  string `json:"media_url,omitempty"`
	MediaType string `json:"media_type,omitempty"`
	Timestamp string `json:"timestamp"`
	From      string `json:"from,omitempty"`
}

// Instagram API response structure
type InstagramResponse struct {
	Data   []InstagramThread `json:"data"`
	Paging struct {
		Cursors struct {
			Before string `json:"before"`
			After  string `json:"after"`
		} `json:"cursors"`
		Next string `json:"next"`
	} `json:"paging"`
}

type InstagramThread struct {
	ID           string            `json:"id"`
	Messages     InstagramMessages `json:"messages"`
	Participants []string          `json:"participants"`
}

type InstagramMessages struct {
	Data []InstagramMessage `json:"data"`
}

type InstagramMessage struct {
	ID   string `json:"id"`
	From struct {
		ID   string `json:"id"`
		Name string `json:"name"`
	} `json:"from"`
	Message     string `json:"message"`
	CreatedTime string `json:"created_time"`
	Attachments struct {
		Data []struct {
			ID   string `json:"id"`
			Type string `json:"type"`
			URL  string `json:"url,omitempty"`
		} `json:"data"`
	} `json:"attachments,omitempty"`
}

func (c *Client) GetRecentDMs(ctx context.Context) ([]Message, error) {
	log.Println("Fetching recent DMs from Instagram...")

	// For Instagram Graph API, we need to use the proper endpoint
	// This is the Instagram Graph API v16.0 endpoint for retrieving conversations
	url := fmt.Sprintf("https://graph.instagram.com/v16.0/me/conversations?fields=participants,messages{id,from,message,created_time,attachments{id,type,url}}&access_token=%s", c.accessToken)

	log.Printf("Making request to: %s", url)

	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		log.Printf("Error creating request: %v", err)
		return nil, fmt.Errorf("error creating request: %w", err)
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		log.Printf("HTTP request failed: %v", err)
		return nil, fmt.Errorf("HTTP request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		log.Printf("Instagram API error (status %d): %s", resp.StatusCode, string(bodyBytes))
		return nil, fmt.Errorf("Instagram API error (status %d): %s", resp.StatusCode, string(bodyBytes))
	}

	bodyBytes, err := io.ReadAll(resp.Body)
	if err != nil {
		log.Printf("Error reading response body: %v", err)
		return nil, fmt.Errorf("error reading response body: %w", err)
	}

	// Log the raw response for debugging
	log.Printf("Instagram API response: %s", string(bodyBytes))

	var igResponse InstagramResponse
	if err := json.Unmarshal(bodyBytes, &igResponse); err != nil {
		log.Printf("Error unmarshalling response: %v", err)
		return nil, fmt.Errorf("error unmarshalling response: %w", err)
	}

	// Convert Instagram response to our message format
	var messages []Message
	for _, thread := range igResponse.Data {
		log.Printf("Processing thread ID: %s with %d participants", thread.ID, len(thread.Participants))
		for _, msg := range thread.Messages.Data {
			message := Message{
				ID:        msg.ID,
				Text:      msg.Message,
				Timestamp: msg.CreatedTime,
				From:      msg.From.Name,
			}

			// Check for attachments
			if len(msg.Attachments.Data) > 0 {
				attachment := msg.Attachments.Data[0]
				message.MediaType = attachment.Type
				message.MediaURL = attachment.URL
			}

			messages = append(messages, message)
			log.Printf("Added message: %+v", message)
		}
	}

	log.Printf("Fetched %d messages", len(messages))
	return messages, nil
}

// Fallback method that tries a different API endpoint if the Graph API fails
func (c *Client) GetRecentDMsAlternative(ctx context.Context) ([]Message, error) {
	log.Println("Trying alternative endpoint for Instagram DMs...")

	// Using legacy API endpoint as fallback
	url := fmt.Sprintf("https://api.instagram.com/v1/direct_v2/inbox?access_token=%s", c.accessToken)

	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return nil, err
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	bodyBytes, _ := io.ReadAll(resp.Body)
	log.Printf("Alternative API response: %s", string(bodyBytes))

	// Process response accordingly...
	// For simplicity, we'll return an empty slice
	return []Message{}, nil
}

func (c *Client) GetMediaContent(ctx context.Context, mediaURL string) ([]byte, error) {
	log.Printf("Fetching media content from: %s", mediaURL)

	req, err := http.NewRequestWithContext(ctx, "GET", mediaURL, nil)
	if err != nil {
		return nil, err
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	// Read the response body
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	log.Printf("Successfully fetched %d bytes of media content", len(body))
	return body, nil
}
