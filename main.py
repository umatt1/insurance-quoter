"""
Insurance Quote Comparison Tool
Compares quotes from different insurance providers using web automation.
"""

import os
import logging
from typing import Optional, List
from pathlib import Path
from pydantic import BaseModel
import asyncio
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from browser_use import Agent, Controller, ActionResult
from browser_use.browser.browser import Browser, BrowserConfig

# Setup logging and environment
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize controller
controller = Controller()

class InsuranceQuote(BaseModel):
    company: str
    monthly_premium: float
    coverage_details: str
    deductible: Optional[float] = None
    coverage_limits: Optional[dict] = None

class QuoteCollection:
    def __init__(self):
        self.quotes: List[InsuranceQuote] = []

    def add_quote(self, quote: InsuranceQuote):
        self.quotes.append(quote)
        logger.info(f"Added quote from {quote.company}: ${quote.monthly_premium}/month")

    def get_best_quote(self) -> Optional[InsuranceQuote]:
        if not self.quotes:
            return None
        return min(self.quotes, key=lambda x: x.monthly_premium)

# Global quote collection
quote_collection = QuoteCollection()

@controller.action("save_insurance_quote", param_model=InsuranceQuote)
def save_insurance_quote(quote: InsuranceQuote) -> ActionResult:
    """Save an insurance quote and display it"""
    quote_collection.add_quote(quote)
    
    display_text = f"""
Found quote from {quote.company}:
Monthly Premium: ${quote.monthly_premium:.2f}
Coverage: {quote.coverage_details}
"""
    if quote.deductible:
        display_text += f"Deductible: ${quote.deductible:.2f}\n"
    if quote.coverage_limits:
        display_text += "Coverage Limits:\n"
        for coverage, limit in quote.coverage_limits.items():
            display_text += f"- {coverage}: {limit}\n"
    
    logger.info(display_text)
    return ActionResult(extracted_content=display_text)

async def get_insurance_quotes(user_data: dict) -> str:
    """Main function to get insurance quotes using web automation"""
    
    # Initialize browser with appropriate configuration
    browser = Browser(
        config=BrowserConfig(
            disable_security=True,
        )
    )

    # Create the agent's task with user data
    task = f"""You are an insurance quote comparison expert. Get car insurance quotes for:
Name: {user_data['name']}
ZIP Code: {user_data['zip_code']}
Vehicle: {user_data['vehicle']}
Email: {user_data.get('email', 'Not provided')}
Phone: {user_data.get('phone', 'Not provided')}

Follow these steps:
1. Visit Progressive's website (https://www.progressive.com/auto/)
2. Fill out the quote form with the user's information
3. Extract and save the quote using save_insurance_quote
4. Visit Auto-Owners' website (https://www.auto-owners.com/insurance/auto)
5. Fill out their quote form
6. Extract and save the quote using save_insurance_quote

Important:
- Make sure to extract accurate premium amounts
- Note all coverage details and limits
- If a form field is not obvious, use reasonable defaults
- If you encounter any errors, try to work around them or provide helpful error messages
"""

    try:
        # Initialize the agent
        agent = Agent(
            task=task,
            llm=ChatOpenAI(model="gpt-4o"),
            controller=controller,
            browser=browser,
        )

        # Run the agent
        result = await agent.run()
        
        # Get the best quote
        best_quote = quote_collection.get_best_quote()
        if best_quote:
            return f"""
Quote Comparison Complete!
Best Option: {best_quote.company}
Monthly Premium: ${best_quote.monthly_premium:.2f}
Coverage: {best_quote.coverage_details}
"""
        else:
            return "No quotes were successfully retrieved. Please try again or contact the insurance companies directly."

    except Exception as e:
        logger.error(f"Error while getting quotes: {str(e)}")
        return f"An error occurred while fetching quotes: {str(e)}"

async def main():
    print("\nWelcome to Insurance Quote Comparison!")
    print("Please provide your details to get quotes from Progressive and Auto-Owners.\n")
    
    # Gather user input
    user_data = {
        "name": input("Enter your name: "),
        "zip_code": input("Enter your zip code: "),
        "vehicle": input("Enter your vehicle details (year, make, model): "),
        "email": input("Enter your email (optional, press enter to skip): ").strip() or None,
        "phone": input("Enter your phone (optional, press enter to skip): ").strip() or None
    }
    
    result = await get_insurance_quotes(user_data)
    print("\n" + result)

if __name__ == "__main__":
    asyncio.run(main())
