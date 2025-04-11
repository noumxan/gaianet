# Instagram Content Safety Checker

A web API that monitors Instagram DMs and uses OpenAI to analyze content for safety and appropriateness.

## Features

- Fetches recent Instagram DMs
- Analyzes text and media content using OpenAI
- Provides safety assessments for:
  - Harmful content
  - Child safety
  - General appropriateness

## Prerequisites

- Go 1.21 or later
- Instagram Business Account with API access
- OpenAI API key

## Configuration

1. Copy `.env.example` to `.env`
2. Fill in the required environment variables:
   - `INSTAGRAM_ACCESS_TOKEN`: Your Instagram Graph API access token
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `SERVER_PORT`: Port to run the server on (default: 8080)

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   go mod download
   ```
3. Run the application:
   ```bash
   go run main.go
   ```

## API Endpoints

- `GET /health`: Health check endpoint
- `GET /messages`: Fetch recent Instagram DMs
- `POST /analyze`: Analyze content using OpenAI

### Analyze Content Request

```json
{
  "content": "Text or media content to analyze"
}
```

### Analyze Content Response

```json
{
  "isHarmful": false,
  "isChildSafe": true,
  "isAppropriate": true,
  "reasoning": "Detailed analysis of the content..."
}
```

## Security Considerations

- Keep your API keys secure
- Use environment variables for sensitive information
- Implement proper rate limiting
- Consider adding authentication for API endpoints

## License

MIT 