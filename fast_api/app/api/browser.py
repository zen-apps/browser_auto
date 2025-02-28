import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from browser_use import Agent, Browser, BrowserConfig
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

browser = APIRouter()


class BrowserTask(BaseModel):
    task: str
    headless: bool = True


class ArticleInfo(BaseModel):
    """Structure for extracted article information"""

    title: str = Field(description="The title of the article")
    summary: str = Field(description="A brief summary of the article content")


def extract_article_info(result) -> dict:
    """Extract article information from browser result"""
    try:
        # Initialize default values
        title = "Minnesota Weather Update"
        summary = None

        # Extract summary from the 'done' action result
        if hasattr(result, "all_results"):
            for action in reversed(result.all_results):
                if getattr(action, "is_done", False) and getattr(
                    action, "extracted_content", None
                ):
                    summary = getattr(action, "extracted_content", None)
                    break

        # If summary isn't found in all_results, try all_model_outputs
        if not summary and hasattr(result, "all_model_outputs"):
            for output in reversed(result.all_model_outputs):
                if (
                    isinstance(output, dict)
                    and "done" in output
                    and "text" in output["done"]
                ):
                    summary = output["done"]["text"]
                    break

        # If we found a summary, use it directly
        if summary:
            logger.info(f"Successfully extracted summary: {summary}")

            # Try to extract location from summary
            location_prefix = ""
            if "minnesota" in summary.lower():
                location_prefix = "Minnesota "

            # Determine type of weather update based on summary content
            weather_type = "Weather Update"
            if any(term in summary.lower() for term in ["wind", "gust"]):
                weather_type = "Wind Advisory"
            elif any(
                term in summary.lower() for term in ["rain", "shower", "precipitation"]
            ):
                weather_type = "Rain Forecast"
            elif any(
                term in summary.lower() for term in ["snow", "flurry", "blizzard"]
            ):
                weather_type = "Snow Forecast"
            elif any(term in summary.lower() for term in ["cold", "chill", "freez"]):
                weather_type = "Cold Weather Alert"
            elif any(term in summary.lower() for term in ["warm", "hot", "heat"]):
                weather_type = "Warm Weather Forecast"
            elif any(
                term in summary.lower() for term in ["storm", "thunder", "lightning"]
            ):
                weather_type = "Storm Warning"

            # Construct a title based on the summary content
            title = f"{location_prefix}{weather_type}"

            return {"title": title, "summary": summary}

        # If we failed to find a summary, try to determine what search was conducted
        search_query = None
        if hasattr(result, "all_results"):
            for action in result.all_results:
                content = getattr(action, "extracted_content", "")
                if content and 'Input "' in content and '" into index' in content:
                    # Extract search query
                    start_idx = content.find('Input "') + 7
                    end_idx = content.find('" into index')
                    if start_idx > 7 and end_idx > start_idx:
                        search_query = content[start_idx:end_idx]
                        break

        if search_query:
            title = f"{search_query.title()} Update"
            default_summary = (
                f"Information about {search_query} could not be retrieved."
            )
        else:
            title = "Weather Update"
            default_summary = "Could not extract weather information."

        return {"title": title, "summary": summary if summary else default_summary}

    except Exception as e:
        logger.error(f"Error extracting article info: {e}", exc_info=True)
        # Return default values in case of error
        return {
            "title": "Minnesota Weather Update",
            "summary": "Weather information could not be retrieved.",
        }


@browser.post("/execute_task/")
async def execute_task(browser_task: BrowserTask):
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
            model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            verbose=False,
        )

        prompt = browser_task.task.strip()

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
        except Exception as gif_error:
            logger.warning(f"Failed to create GIF: {gif_error}")
            gif_relative_path = None

        # Log the raw result for debugging
        logger.info(f"Task result: {result}")

        """
        class InventoryQuery(BaseModel):
    make: str = Field(description="The make of the car")
    model: Optional[str] = Field(description="The model of the car")
    year: Optional[str] = Field(description="The year of the car")
            structured_llm = llm.with_structured_output(InventoryQuery)
        car_info = structured_llm.invoke(messages)
    """

        class ExtractWebsiteInfo(BaseModel):
            title: str = Field(description="The title of the website")
            summary: str = Field(description="A brief summary of the website content")

        structured_llm = model.with_structured_output(ExtractWebsiteInfo)
        messages = [
            SystemMessage(
                content="You are a helpful assistant that extracts information from websites."
            ),
            HumanMessage(content=str(result)),
        ]
        article_info = structured_llm.invoke(messages)
        # Prepare the response
        response_data = {
            "article_title": article_info.title,
            "article_summary": article_info.summary,
        }

        logger.info("Task completed successfully")
        return response_data

    except Exception as e:
        logger.error(f"Error executing browser task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
