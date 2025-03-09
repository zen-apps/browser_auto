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
    company_name: str
    headless: bool = True


@browser.post("/execute_task/")
async def execute_task(browser_task: BrowserTask):
    try:
        # Create screenshots directory if it doesn't exist
        screenshots_dir = Path("/var/log/screenshots")
        screenshots_dir.mkdir(exist_ok=True, parents=True)

        browser_task_dict = {
            "task": f"""
            go to https://importyeti.com.
            wait for page to load completely.
            
            Go to search bar, type in {browser_task.company_name} and click enter.
            Wait for page to load.
            Click on the first result listed.
            Wait for page to load.
            Go to '{browser_task.company_name}' Suppliers section.
            Copy all data in the section and return as JSON
            """,
            "headless": browser_task.headless,  # Use attribute notation here too
        }

        browser_config = BrowserConfig(
            headless=browser_task_dict["headless"],
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

        prompt = browser_task_dict["task"].strip()

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

        class ExtractWebsiteInfo(BaseModel):
            suppliers: List[str] = Field(
                description="Names of suppliers for Hormel Foods"
            )
            countries: List[str] = Field(
                description="Countries where suppliers are located"
            )
            shipment_activity: str = Field(
                description="Time period of shipment activity"
            )
            total_shipments: List[int] = Field(
                description="Number of shipments per supplier"
            )
            product_descriptions: List[str] = Field(
                description="Product descriptions for each supplier"
            )

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
            "suppliers": article_info.suppliers,
            "countries": article_info.countries,
            "shipment_activity": article_info.shipment_activity,
            "total_shipments": article_info.total_shipments,
            "product_descriptions": article_info.product_descriptions,
            "gif_path": gif_relative_path,
            "raw_result": result,
        }

        logger.info("Task completed successfully")
        return response_data

    except Exception as e:
        logger.error(f"Error executing browser task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
