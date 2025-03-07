# -*- coding: utf-8 -*-
"""Agent ai using Langgraph.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1abYJ3g9o9t_KyS19JIf7srWSOm21Wy94
"""

pip install langchain-core langchain-google-genai langgraph google-generativeai

!pip install langgraph --upgrade langchain-core python-dotenv

import os
os.environ["GOOGLE_API_KEY"] = "AIzaSyCY0mUiFwCi75aPQBcwRXwlw_dQnkqzGro"

import langchain_core.callbacks as callbacks
print(dir(callbacks))

import langchain_core
print(langchain_core.__version__)

from typing import Annotated, Any, Dict, List, Sequence, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
from langchain_core.tools import BaseTool
from langchain_core.callbacks import CallbackManager  # Use CallbackManager instead
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import os

# Example usage of CallbackManager if needed:
callback_manager = CallbackManager([])

# Define our state
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], "The messages in the conversation"]
    next: str

class Calculator(BaseTool):
    name: str = "calculator"  # Add type annotation for name
    description: str = "Useful for performing mathematical calculations"  # Add type annotation for description

    def _run(self, input_text: str) -> str:
        try:
            return str(eval(input_text))
        except Exception as e:
            return f"Error in calculation: {str(e)}"

# Create the agent prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful AI assistant that can use tools to accomplish tasks. "
              "When you need to use a tool, respond with the tool name and input in the format: "
              "TOOL: calculator\nINPUT: <mathematical expression>\n "
              "Otherwise, respond directly to the user."),
    MessagesPlaceholder(variable_name="messages"),
])

# Initialize the Gemini model
model = ChatGoogleGenerativeAI(
    model="gemini-pro",
    temperature=0,
    convert_system_message_to_human=True  # Gemini doesn't support system messages directly
)

# Define tools
tools = [Calculator()]
tool_executor = ToolExecutor(tools)

# Function to determine the next step
def should_use_tool(state: AgentState) -> Dict[str, Any]:
    """Determine if we should use a tool or respond to the user."""
    messages = state["messages"]
    response = model.invoke(
        prompt.format(messages=messages)
    )

    # Check if the response indicates tool usage
    # Looking for the TOOL: format we specified in the prompt
    if "TOOL:" in response.content:
        return {"next": "tool"}
    else:
        return {"next": "end"}

# Function to call tools
def call_tool(state: AgentState) -> Dict[str, Any]:
    """Call the appropriate tool based on the agent's decision."""
    messages = state["messages"]
    response = model.invoke(
        prompt.format(messages=messages)
    )

    try:
        # Parse the tool response format
        tool_section = response.content.split("TOOL:")[1].strip()
        tool_name = tool_section.split("\n")[0].strip().lower()
        input_section = tool_section.split("INPUT:")[1].strip()
        tool_input = input_section.split("\n")[0].strip()

        # Execute the tool
        tool_result = tool_executor.invoke({"name": tool_name, "input": tool_input})

        # Add tool result to messages
        new_messages = list(messages)
        new_messages.append(AIMessage(content=f"Tool result: {str(tool_result)}"))
        return {"messages": new_messages, "next": "agent"}
    except Exception as e:
        print(f"Error in tool execution: {str(e)}")
        return {"messages": messages, "next": "end"}

# Function for final response
def generate_response(state: AgentState) -> Dict[str, Any]:
    """Generate the final response to the user."""
    messages = state["messages"]
    response = model.invoke(
        prompt.format(messages=messages)
    )

    new_messages = list(messages)
    new_messages.append(response)
    return {"messages": new_messages, "next": END}

# Create the graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("agent", should_use_tool)
workflow.add_node("tool", call_tool)
workflow.add_node("end", generate_response)

# Add edges
workflow.add_edge("agent", "tool")
workflow.add_edge("agent", "end")
workflow.add_edge("tool", "agent")

# Add an edge from START to the initial node "agent"
from langgraph.graph import START # Import START node
workflow.add_edge(START, "agent") # Connect START to the first node

# Compile the graph
app = workflow.compile()

# Function to run the agent
def run_agent(input_text: str) -> List[BaseMessage]:
    """Run the agent with the given input."""
    result = app.invoke({
        "messages": [HumanMessage(content=input_text)],
        "next": "agent"
    })
    return result["messages"]

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    GOOGLE_API_KEY = getpass("Enter your Google API Key: ")
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

# Initialize the chat model
chat_model = ChatGoogleGenerativeAI(model="gemini-pro", api_key=os.environ["GOOGLE_API_KEY"])

# Define the agent logic for continuous chat
def chat_with_api():
    print("Chat session started! Type 'exit' to end the chat.\n")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit']:
            print("Chat session ended. Goodbye!")
            break
        response = chat_model.invoke(user_input)
        print(f"AI: {response.content}")

# Start the chat
if __name__ == "__main__":
    chat_with_api()

