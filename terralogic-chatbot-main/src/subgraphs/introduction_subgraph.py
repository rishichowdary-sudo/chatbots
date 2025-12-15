from typing import Literal, Annotated, List, Dict, Optional

from langchain_core.prompts import PromptTemplate
from langgraph.graph import StateGraph, START, END
from langgraph.graph import MessagesState
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, AIMessage
from langgraph.prebuilt import ToolNode, tools_condition

# from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
# from langchain_cohere import ChatCohere

from langgraph.checkpoint.memory import MemorySaver
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from dotenv import load_dotenv

import os
import json
from IPython.display import Image, display
import sys
import configparser

sys.path.append(os.getcwd())
load_dotenv()
from src.tools.email_Validator import validate_email_address


from pydantic import BaseModel, Field
class ResponseFormatter(BaseModel):
    """Always use this tool to structure your response to the user."""
    answer: str = Field(description="The answer to the user's question")
    name_collected_validated: str = Field(description="Name collected from the user that has been validated")
    email_collected_validated: str = Field(description="Email collected from the user that has been validated")
    name_reasoning: str = Field(description = "Reasoning for accepting the name as valid against the name validation instructions provided")
    email_reasoning: str = Field(description = "Reasoning behind why the extract_email tool call was not made for email extraction and validation")

class OverallState(MessagesState):
    # messages is implicit
    name: str
    email: str
    mode: str
    chatMessageOptions: List[str]

class ServiceInformationSubgraph:
    def __init__(self, llm, decision_llm, all_prompts):
        self.llm = llm
        self.decision_llm = decision_llm
        self.all_prompts = all_prompts

        self.tools = [self.extract_email, ResponseFormatter]
        self.llm_with_tools = self.llm.bind_tools(self.tools, parallel_tool_calls = False, tool_choice='any') 
        self.llm_with_structure = self.llm_with_tools.with_structured_output(ResponseFormatter)


    def extract_email(self, user_input: str) -> Dict[str, Optional[str]]:
        """
        Tool to extract email from user input, if available.

        Args:
            user_input: The user input text.

        Returns:
            Dict[str, Optional[str]]: A dictionary with string keys and values 
        """

        prompt = PromptTemplate(template = self.all_prompts["extract_name_email_template"], input_variables=["text"])
        chain = prompt | self.llm | JsonOutputParser()

        decision = chain.invoke({"text": user_input})
        user_email = decision["email"] if decision["email"] != "" else None
        email_validation_reason = None

        if user_email is not None:
            is_valid, email_validation_reason = validate_email_address(user_email)
            if not is_valid:
                user_email = None

        return {"user_email": user_email, "email_validation_reason": email_validation_reason}


    # Introduction Node
    def introduction_node(self, state: OverallState):
        """
        Node that greets the user, collects user's name, emailID and tells the service that the chat server can offer.

        Args:
            state (OverallState): state message containing messages, name, email, mode and chatMessageOptions
        
        Returns: 
            state (OverallState): state message with extracted user name and email.

        """
        
        output = self.llm_with_tools.invoke([self.all_prompts["service_intro_template"]] + state["messages"])

        return {"messages": output}
        
        # Define the function that responds to the user
    def respond(self, state: OverallState):
        # Construct the final answer from the arguments of the last tool call
        email_tool_call = state["messages"][-1].tool_calls[0]
        output = ResponseFormatter(**email_tool_call["args"])
        # Since we're using tool calling to return structured output,
        # we need to add  a tool message corresponding to the WeatherResponse tool call,
        # This is due to LLM providers' requirement that AI messages with tool calls
        # need to be followed by a tool message for each tool call
        tool_message = {
            "type": "tool",
            "content": "Here is your structured response",
            "tool_call_id": email_tool_call["id"],
        }
        
        # check if the user_name and user_email is already present.
        user_name = state.get("name", None)
        user_email = state.get("email", None)
        extracted_name, extracted_email = "", ""

        response = AIMessage(content=output.answer)
        extracted_name = output.name_collected_validated
        extracted_email = output.email_collected_validated

        user_name = extracted_name if extracted_name != "" else user_name
        user_email = extracted_email if extracted_email != "" else user_email

        # if either of user_name or user_email is not given, we continue in introducing mode. Still need to get them.
        if user_name is None or user_email is None:
            return {"messages": [tool_message, response], "name": user_name, "email": user_email, "mode": "introducing"}
        else:
            # name, email required fields are filled. Now going to go in answering mode with options.
            chatMessageOptions=["Start a project", "Looking for a job", "Explore services"]
            return {"messages": [tool_message, response], "name": user_name, "email": user_email, "mode": "answering", "chatMessageOptions": chatMessageOptions}
    
    # Define the function that determines whether to continue or not
    def should_continue(self,  state: OverallState):
        messages = state["messages"]
        last_message = messages[-1]
        # If there is only one tool call and it is the response tool call we respond to the user
        if (
            len(last_message.tool_calls) == 1
            and last_message.tool_calls[0]["name"] == "ResponseFormatter"
        ):
            return "respond"
        # Otherwise we will use the tool node again
        else:
            return "continue"


    def build_graph(self):

        graph_builder = StateGraph(OverallState)

        # add nodes
        graph_builder.add_node("introduction_node", self.introduction_node)
        graph_builder.add_node("respond", self.respond)
        graph_builder.add_node("tools", ToolNode(self.tools))

        # build edges
        graph_builder.set_entry_point("introduction_node")
        # We now add a conditional edge
        graph_builder.add_conditional_edges(
            "introduction_node",
            self.should_continue,
            {
                "continue": "tools",
                "respond": "respond",
            },
        )

        graph_builder.add_edge("tools", "introduction_node")
        graph_builder.add_edge("respond", END)

        # memory object
        memory = MemorySaver()

        # compile graph
        graph = graph_builder.compile(checkpointer=memory)
        return graph    




def stream_graph_updates(user_input: str, config: dict):
    for event in graph.stream({"messages": [("user", user_input)]}, config):
        for value in event.values():
            print("Assistant: ", value["messages"][-1].content)




if __name__ == "__main__":
    print("We begin")

    prompts_config = configparser.ConfigParser()
    client = "terralogic"
    root_dir = os.path.join('Data', client)
    prompts_config.read(os.path.join(root_dir, 'system_prompts.ini'))
    all_prompts = prompts_config["prompts"]

    # llm object creation
    # llm = ChatCohere(model='command-r-plus-08-2024')
    # decision_llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=os.getenv("GOOGLE_API_KEY"))
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    decision_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    
    introduction_subgraph = ServiceInformationSubgraph(llm, decision_llm, all_prompts)
    graph = introduction_subgraph.build_graph()
    
    config = {"configurable": {"thread_id": "1"}}

    # uncomment to view the graph
    # with open("ServiceInformation.png", "wb") as png:
    #     png.write(graph.get_graph(xray=1).draw_mermaid_png())
    
    
    while True:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        messages = [HumanMessage(content=user_input)]
        # stream_graph_updates(user_input, config)
        messages = graph.invoke({"messages": messages}, config)
        for m in messages["messages"]:
            m.pretty_print()
