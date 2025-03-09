# Browser Auto

An automated browser system for scraping company supplier data from ImportYeti, with built-in capabilities to handle Cloudflare Captcha challenges in a headless environment.

## Overview

This project provides a FastAPI backend service that uses Playwright for browser automation and LangChain with OpenAI for AI-assisted web browsing and data extraction. The system is designed to:

1. Launch a browser session (headless or visible)
2. Navigate to ImportYeti.com
3. Search for a specified company
4. Extract supplier information
5. Return structured JSON data
6. Create a GIF showing the browsing session

## Requirements

- Docker and Docker Compose
- OpenAI API key
- Virtual machine with at least 2GB RAM

## Setup Instructions

1. Clone this repository to your VM:
   ```bash
   git clone <repository_url> browser_auto
   cd browser_auto
   ```

2. Update the configuration file with your OpenAI API key:
   ```bash
   # Edit config/dev.env
   OPENAI_API_KEY=<your_openai_api_key_here>
   ```

3. Build and start the Docker container:
   ```bash
   docker-compose -f docker-compose-dev.yml up -d --build
   ```

4. Verify the API is running:
   ```bash
   curl http://<vm_ip>:1099/
   ```

## Using the API

The main endpoint for executing browser tasks is `/v1/browser/execute_task/`. Here's how to use it:

### Example API Request

```bash
curl -X POST http://<vm_ip>:1099/v1/browser/execute_task/ \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "kraft foods",
    "headless": true
  }'
```

### Request Parameters

- `company_name`: The name of the company to search for on ImportYeti
- `headless`: Boolean flag to determine if the browser should run in headless mode (recommended: true)

### Response

The API will return a JSON response with the following structure:

```json
{
  "suppliers": ["Supplier 1", "Supplier 2", ...],
  "countries": ["Country 1", "Country 2", ...],
  "shipment_activity": "Jan 2023 - Dec 2023",
  "total_shipments": [10, 20, ...],
  "product_descriptions": ["Description 1", "Description 2", ...],
  "gif_path": "screenshots/task_history_20250303_171215.gif",
  "raw_result": "Raw data from the browser automation"
}
```

## Handling Cloudflare Captcha

This system is designed to pass Cloudflare Captcha challenges in a headless environment through:

1. Appropriate browser configuration (user-agent, headers, etc.)
2. AI-assisted browser automation for detecting and solving challenges
3. Maintaining browser state between sessions

For optimal Cloudflare bypass performance, consider:
- Keeping a valid cookie session in the logs/browser_data directory
- Ensuring your VM IP is not rate-limited
- Running in headless mode with appropriate timeouts

## Troubleshooting

- If you encounter "Browser not available" errors, check Docker logs:
  ```bash
  docker-compose -f docker-compose-dev.yml logs fast_api_backend
  ```

- For Cloudflare issues, inspect screenshots in the logs/screenshots directory
- For API errors, check logs/app.log

## Project Structure

- `fast_api/`: FastAPI application
  - `app/`: Application code
    - `api/`: API endpoints
      - `browser.py`: Browser automation endpoints
  - `Dockerfile`: Docker configuration
- `config/`: Environment configuration
- `logs/`: Log files and screenshots
- `data/`: Data storage

## Notes

- The system requires significant memory (at least 2GB) for the browser
- Browser sessions are isolated in Docker containers
- Browser automation might be detected by some websites