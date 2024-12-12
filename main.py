from browser_use import Agent, Browser, Controller
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
import asyncio
import os
from typing import Optional

class InsuranceQuote(BaseModel):
    company: str
    monthly_premium: float
    coverage_details: str
    deductible: Optional[float] = None

class UserDetails(BaseModel):
    name: str
    zip_code: str
    vehicle_details: str
    email: Optional[str] = None
    phone: Optional[str] = None

class InsuranceQuoter:
    def __init__(self):
        self.controller = Controller()
        self.quotes = []
        self.setup_actions()

    def setup_actions(self):
        @self.controller.action("save_quote", param_model=InsuranceQuote)
        async def save_quote(params: InsuranceQuote):
            self.quotes.append(params)
            print(f"\nFound quote from {params.company}:")
            print(f"Monthly Premium: ${params.monthly_premium:.2f}")
            print(f"Coverage: {params.coverage_details}")
            if params.deductible:
                print(f"Deductible: ${params.deductible:.2f}")
            print("-" * 50)

    async def get_quotes(self) -> str:
        # Initialize the language model
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Please set OPENAI_API_KEY environment variable")

        llm = ChatOpenAI(model="gpt-4", api_key=api_key)
        
        # Get user input
        print("\nWelcome to Insurance Quote Comparison!")
        print("Please provide your details to get quotes from Progressive and Auto-Owners.\n")
        
        user_name = input("Enter your name: ")
        zip_code = input("Enter your zip code: ")
        vehicle_details = input("Enter your vehicle details (year, make, model): ")
        email = input("Enter your email (optional, press enter to skip): ").strip() or None
        phone = input("Enter your phone (optional, press enter to skip): ").strip() or None

        user_data = UserDetails(
            name=user_name,
            zip_code=zip_code,
            vehicle_details=vehicle_details,
            email=email,
            phone=phone
        )

        # Create browser instance with appropriate configuration
        browser = Browser(
            browser_config={
                "headless": False  # Set to True in production
            },
            browser_context_config={
                "bypass_csp": True,  # Disable security for better compatibility
            },
            page_config={
                "minimum_wait_page_load_time": 2,
                "wait_for_network_idle_page_load_time": 5,
                "maximum_wait_page_load_time": 30
            }
        )

        try:
            async with browser.new_context() as context:
                agent = Agent(
                    task=f"""
                    Get car insurance quotes for the following user:
                    Name: {user_data.name}
                    ZIP: {user_data.zip_code}
                    Vehicle: {user_data.vehicle_details}
                    Email: {user_data.email if user_data.email else 'Not provided'}
                    Phone: {user_data.phone if user_data.phone else 'Not provided'}

                    Follow these steps:
                    1. Visit Progressive's website (https://www.progressive.com/auto/)
                    2. Fill out the quote form with the user's information
                    3. Save the quote details using the save_quote action
                    4. Open a new tab and visit Auto-Owners' website (https://www.auto-owners.com/insurance/auto)
                    5. Fill out their quote form
                    6. Save the quote details using the save_quote action
                    7. Compare the quotes and provide a recommendation based on price and coverage
                    """,
                    llm=llm,
                    controller=self.controller,
                    browser_context=context,
                    max_steps=20
                )
                
                result = await agent.run()
                
                if self.quotes:
                    lowest_quote = min(self.quotes, key=lambda x: x.monthly_premium)
                    return f"\nRecommendation:\nBased on the quotes received, {lowest_quote.company} offers the best value with a monthly premium of ${lowest_quote.monthly_premium:.2f}"
                else:
                    return "\nNo quotes were successfully retrieved. Please try again or contact the insurance companies directly."
                    
        except Exception as e:
            return f"An error occurred while fetching quotes: {str(e)}"

async def main():
    quoter = InsuranceQuoter()
    result = await quoter.get_quotes()
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
