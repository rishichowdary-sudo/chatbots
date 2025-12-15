import sys
import os
sys.path.append(os.getcwd())

import requests
from bs4 import BeautifulSoup
from typing import Literal, Annotated, List, Dict, Optional

from langchain_core.prompts import PromptTemplate
from langgraph.graph import StateGraph, START, END
from langgraph.graph import MessagesState
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage,  AIMessage
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.tools import tool, BaseTool
from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
# from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

# from src.all_prompts import job_params_template
from utils.logger_config import logger
import configparser
import yaml, json
from dotenv import load_dotenv

load_dotenv()



class OverallState(MessagesState):
    chatMessageOptions: List[str]
    jobs : List


from bs4 import BeautifulSoup
import requests

class JobItem(BaseModel):
    title: str = Field(description="Job title")
    location: str = Field(description="Job location")
    link: str = Field(description="URL for job application")

class Response_format(BaseModel):
    response: str = Field(description="Conversational reply to the user's question that does not contain any direct job listings.")
    filtered_jobs: List[JobItem] = Field(description="List of filtered jobs, each containing 'title', 'location', and 'link'.")
    reasoning: str = Field(description="Your reasoning for gving this answer and whether you have followed the guidelines.")


class CareerToolNode:
    """Search for available jobs on a career website based on job type and location, providing the link."""

    def __init__(self, llm, client_properties, all_prompts):
        self.jobtype = ""
        self.location = ""
        self.filtered_jobs =[]
        self.url = client_properties.get('CAREER_URL')
        self.llm = llm
        self.all_prompts = all_prompts
        self.tools = [self.extract_job_params]
        #self.llm_with_Tool = self.llm.bind_tools(self.tools, parallel_tool_calls = False)
        self.llm_with_structured_output = self.llm.with_structured_output( Response_format)
        self.career_llm = self.define_career_llm()
#        self.filtering_llm = self.filtering_llm()

    def define_career_llm(self):
        prompt = PromptTemplate(
            template=self.all_prompts["job_params_template"],
            input_variables=['chat_history', 'jobs'],
        )
        chain = prompt | self.llm_with_structured_output
        return chain

    # def filtering_llm(self):
    #     prompt = PromptTemplate(
    #         template=self.all_prompts["job_filters_template"],
    #         input_variables=['jobs', 'jobtype', 'location'],
    #     )
    #     chain = prompt | self.llm | JsonOutputParser()
    #     return chain

    def extract_job_params(self) -> List:
        """
        This node filters the job based on the jobtype and location 

        args:
            jobtype, location
        
        Returns: 
            filtered jobs based on the jobtype and location
        
        """
        try:
            response = requests.get(
                self.url,
                verify=False,
                timeout=30
                )
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")
            job_elements = soup.find_all('li', class_='open-ticket-list__item')
                
            jobs = []
            for job_element in job_elements:
                # Extract job title
                title_element = job_element.find('h6', class_='fnt-18 clr-white fnt-600 m-0')
                title = title_element.text.strip() if title_element else 'N/A'

                # Extract job location
                Location_element = job_element.find('span', class_='d-inline-block fnt-400 fnt-14 clr-white text-right')
                Location = Location_element.text.strip() if Location_element else 'N/A'

                # Extract the application link
                link_element = job_element.find('a', class_='d-flex')
                link = link_element['href'].strip() if link_element else 'N/A'

                # Filter based on job type and location
                # if jobtype not in (None, "", "None") and jobtype.lower() not in title.lower():
                #     continue
                # if location not in (None, "", "None") and location.lower() not in Location.lower():
                #     continue
                
                #jobs.append(f"Title: {title}\nLocation: {loc}\nApply here: {link}\n")
                #jobs.append(f"<b><i>Title</b></i>: {title}<br> <b><i>Location</b></i>: {Location}<br> <b><i>Apply here</b></i>: <a href='{link}' target='_blank' rel='noopener noreferrer'>Apply</a>")
                jobs.append([title, Location, link])
                #print(self.career_llm.invoke({'chat_history': messages, 'jobs': jobs}))

            return jobs

            # output = self.filtering_llm.invoke({'jobs' : jobs, 'jobtype' : jobtype, 'location': location })
            # self.filtered_jobs = output.get("filtered_jobs", [])
            # print(self.filtered_jobs)
            # return {
            #     'messages': [
            #         ToolMessage(
            #             content=output,  # Convert output to string if needed
            #             tool_call_id='job_search',  # Add this if ToolMessage requires it
            #             tool_name="extract_job_params"
            #         )
            #     ]
            # }

        except requests.RequestException as e:
            logger.exception(f"Career request at _run_search_jobs() failed with exception: {e}")
            return None
            # return {
            #     'messages': [
            #         ToolMessage(
            #             content='Oops, I dont have the job list right now. Try again later',
            #             tool_call_id='job_search_error',
            #             tool_name="extract_job_params"
            #         )
            #     ]
            # }

    def _run_search_jobs(self, state):
        messages = state['messages']
        last_message = messages[-1]


        jobs = self.extract_job_params()
        model_response = self.career_llm.invoke({'chat_history': messages[-10:], 'jobs': jobs})

        output = model_response
        response = output.response
        filtered_jobs = output.filtered_jobs
        formatted_filtered_jobs = []
        for job in filtered_jobs:
            job_html = (
                f"<b><i>Title</i></b>: {job.title}<br> "
                f"<b><i>Location</i></b>: {job.location}<br> "
                f"<b><i>Apply here</i></b>: <a href='{job.link}' target='_blank' rel='noopener noreferrer'>Apply</a>"
            )
            formatted_filtered_jobs.append(job_html)

        return {'messages': [AIMessage(content= response)], 'jobs': formatted_filtered_jobs, 'chatMessageOptions':[]}
        

        # # If the last message is from the user, invoke the model to get tool call
        # if isinstance(last_message, HumanMessage):
            
        #     print(model_response)
        #     #output = json.loads(model_response.content)
        #     #response = output.get("response", None)
        #     #filtered_jobs = output.get("filtered_jobs", [])

        #     return {'messages': [model_response], 'jobs': self.filtered_jobs , 'chatMessageOptions':[]}
        
        # # If the last message is a ToolMessage, process the tool result
        # elif isinstance(last_message, ToolMessage):
        #     filtered_jobs = last_message.content  # Assuming content contains the filtered jobs
        #     llm_response = self.career_llm.invoke({
        #     'chat_history': messages[-15:] + [
        #         ToolMessage(content=f"Here are the job search results: {filtered_jobs}")
        #         ]
        #     })

        #     print(llm_response)

        #     llm_response = json.loads(llm_response)
        #     response = llm_response.get("response", None)
        #     filtered_jobs = llm_response.get("filtered_jobs", [])

        #     return {'messages': [AIMessage(content= response)], 'jobs': filtered_jobs, 'chatMessageOptions':[]}
 
        
        # Fallback for unexpected message types
        # else:
        #     return {'messages': [AIMessage(content="Sorry, I encountered an error.")]}
    

    def build_graph(self):
        graph_builder = StateGraph(OverallState)

        #add nodes
        graph_builder.add_node("job_search", self._run_search_jobs)
        #graph_builder.add_node("tools", ToolNode(self.tools))

        #add edges
        graph_builder.add_edge( START, "job_search")
        #graph_builder.add_conditional_edges("job_search", tools_condition)
        graph_builder.add_edge( "job_search", END)

        memory = MemorySaver()

        graph = graph_builder.compile(checkpointer= memory)
        
        return graph

    

    

if __name__ == "__main__":
    print("We begin")

    prompts_config = configparser.ConfigParser()
    client = "lollypop_design"
    root_dir = os.path.join('Data', client)
    prompts_config.read(os.path.join(root_dir, 'system_prompts.ini'))
    all_prompts = prompts_config["prompts"]

    # llm object creation
    # llm = ChatCohere(model='command-r-plus-08-2024')
    # decision_llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=os.getenv("GOOGLE_API_KEY"))
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    decision_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    def _load_prompts( client_properties):
        prompts_config = configparser.ConfigParser()
        prompts_file_path = os.path.join(client_properties["ROOT_DIR"], client_properties["CLIENT_NAME"], client_properties["SYSTEM_PROMPTS_FILE"])
        prompts_config.read(prompts_file_path)
        all_prompts = prompts_config["prompts"]
        return all_prompts
    
    def _load_properties( client):
        with open("client_properties.yaml") as file:
            client_properties = yaml.safe_load(file)
            client_properties = client_properties[client]
            return client_properties 

    client_properties = _load_properties(client)   
    all_prompts = _load_prompts(client_properties)

    career_subgraph = CareerToolNode(llm, client_properties, all_prompts)
    graph = career_subgraph.build_graph()
    
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