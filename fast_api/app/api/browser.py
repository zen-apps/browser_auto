import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from browser_use import Agent, Browser, BrowserConfig
from langchain_openai import ChatOpenAI
import html2text
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

browser = APIRouter()


class BrowserTask(BaseModel):
    task: str
    headless: bool = True


def extract_title_and_summary(result: dict) -> tuple:
    """Extract both the article title and summary from the browser result."""
    title = None
    summary = None

    if isinstance(result, dict):
        # Get title from history
        if "history" in result:
            for step in reversed(result["history"]):
                if "state" in step and "tabs" in step["state"]:
                    for tab in step["state"]["tabs"]:
                        if "title" in tab and tab["title"]:
                            title = tab["title"]
                            break
                    if title:
                        break

        # Get summary from last done action
        if "history" in result:
            for step in reversed(result["history"]):
                if "model_output" in step and "action" in step["model_output"]:
                    for action in step["model_output"]["action"]:
                        if isinstance(action, dict) and "done" in action:
                            if "text" in action["done"]:
                                summary = action["done"]["text"]
                                break
                    if summary:
                        break

    return title, summary


@browser.post("/execute_task/")
async def execute_task(browser_task: BrowserTask):
    logger.info(f"Received browser task: {browser_task.task}")
    try:
        # Create screenshots directory if it doesn't exist
        screenshots_dir = Path("/var/log/screenshots")
        screenshots_dir.mkdir(exist_ok=True, parents=True)

        browser_config = BrowserConfig(
            headless=browser_task.headless,
            extra_chromium_args=[
                "--disable-web-security",
                "--disable-gpu",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-extensions",
                "--disable-infobars",
                "--start-maximized",
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            ],
        )

        logger.info("Initializing browser...")
        browser_instance = Browser(config=browser_config)

        logger.info("Setting up OpenAI model...")
        model = ChatOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            model=os.getenv("OPENAI_MODEL", "gpt-4"),
        )

        prompt = browser_task.task.strip()
        # {
        #   "task": "go to https://news.google.com/home?hl=en-US&gl=US&ceid=US:en.  wait for page to load.  Go to search bar, type in Donald Trump and click enter.  Wait for page to load.  The click on the first article listed.  Wait for page to load.  Summarize the article in less than 20 words.",
        #   "headless": true
        # }
        logger.info("Creating agent...")
        agent = Agent(
            task=prompt,
            llm=model,
            browser=browser_instance,
        )

        logger.info("Running task...")
        result = await agent.run()

        # Generate unique filename for the GIF
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        gif_path = screenshots_dir / f"task_history_{timestamp}.gif"

        try:
            # Save GIF to file
            agent.create_history_gif(output_path=str(gif_path))
            gif_relative_path = f"screenshots/task_history_{timestamp}.gif"
            logger.info(f"Created GIF at {gif_path}")
        except Exception as gif_error:
            logger.warning(f"Failed to create GIF: {gif_error}")
            gif_relative_path = None

        # Extract title and summary
        title, summary = extract_title_and_summary(result)

        # Log the extracted information for debugging
        logger.info(f"Extracted title: {title}")
        logger.info(f"Extracted summary: {summary}")

        # Prepare the response
        response_data = {
            "title": title,
            "summary": summary,
            "gif_path": gif_relative_path,
        }

        logger.info("Task completed successfully")
        return response_data

    except Exception as e:
        logger.error(f"Error executing browser task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
