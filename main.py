from browser_use import Agent
from langchain_openai import ChatOpenAI
from browser_use.agent.service import Controller
from pydantic import BaseModel
import asyncio

# Define parameters for the custom action to retrieve user input
class UserDetails(BaseModel):
    name: str
    zip_code: str
    vehicle_details: str

# Initialize controller
controller = Controller()

@controller.action('Ask user for insurance details', param_model=UserDetails)
def get_user_details(params: UserDetails):
    print(f"\nThank you, {params.name}!")
    print("Fetching quotes for your zip code and vehicle details...")
    return params

async def retrieve_and_compare_insurance_quotes():
    # Define the language model to use (OpenAI GPT-4 model in this case)
    llm = ChatOpenAI(model="gpt-4o")

    # Define the task
    task = (
        "Retrieve car insurance quotes from Progressive and Auto-Owners' websites "
        "based on the user's name, zip code, and vehicle details, then compare the results."
    )

    # Create the agent
    agent = Agent(
        task=task,
        llm=llm,
        controller=controller,
    )

    # Prompt the user for information
    user_name = input("Enter your name: ")
    zip_code = input("Enter your zip code: ")
    vehicle_details = input("Enter your vehicle details (e.g., year, make, model): ")

    # Register the input data into the agent's task
    controller.register_action(
        'Retrieve user input',
        lambda: UserDetails(name=user_name, zip_code=zip_code, vehicle_details=vehicle_details)
    )

    # Run the agent
    result = await agent.run()
    print("\nResults:\n", result)

if __name__ == "__main__":
    asyncio.run(retrieve_and_compare_insurance_quotes())
