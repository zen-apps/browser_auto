import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from browser_use import Agent, Browser, BrowserConfig
from langchain_openai import ChatOpenAI
import asyncio
import html2text
import logging

logger = logging.getLogger(__name__)

browser = APIRouter()


class BrowserTask(BaseModel):
    task: str
    headless: bool = True


@browser.post("/execute_task/")
async def execute_task(browser_task: BrowserTask):
    logger.info(f"Received browser task: {browser_task.task}")
    try:
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

        logger.info("Creating agent...")
        agent = Agent(
            task=browser_task.task,
            llm=model,
            browser=browser_instance,
        )

        logger.info("Running task...")
        result = await agent.run()
        logger.info("Task completed successfully")
        return {"result": result}
    except Exception as e:
        logger.error(f"Error executing browser task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
