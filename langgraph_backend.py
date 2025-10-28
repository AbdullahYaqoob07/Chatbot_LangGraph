
from langgraph.graph import StateGraph, START,END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage,HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
from langgraph.checkpoint.sqlite import SqliteSaver
from dotenv import load_dotenv
import sqlite3
import os

load_dotenv()
os.environ["OPENAI_API_KEY"] =os.getenv("OPENAI_API_KEY") # pyright: ignore[reportArgumentType]


llm = ChatOpenAI(model="gpt-4o-mini", temperature=0) # pyright: ignore[reportArgumentType]
conn=sqlite3.connect(database='chatbot.db', check_same_thread=False)

search_tool=DuckDuckGoSearchRun(region='us-en') # pyright: ignore[reportCallIssue]

@tool
def calculator(first_num:float, second_num:float, operation:str)->dict: # pyright: ignore[reportReturnType]
    """""
    Perform a basic arithemtic operations on two numbers.
    Supported operations: add,sub,div,mul
    """
    try:
        if operation=='add':
            result=first_num+second_num
        elif operation=='sub':
            result=first_num-second_num
        elif operation=='mul':
            result=first_num*second_num
        elif operation=='div':
            if second_num==0:
                return {"error": "Division is not allowed by zero"}
            result=first_num/second_num
        else:
            return {"error": f"Unsupported operation '{operation}'"}
        return {'first_num':first_num, 'second_num':second_num,"operation":operation,'result':result}
    except Exception as e:
        return {'error':str(e)}

tools=[search_tool, calculator]
llm_with_tools= llm.bind_tools(tools)


class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def chat_node(state: ChatState):
    #take user query from state
    messages=state['messages']
    #send to llm
    response=llm_with_tools.invoke(messages) # pyright: ignore[reportCallIssue]
    #response store state
    return {'messages':[response]}

tool_node=ToolNode(tools)

checkpointer=SqliteSaver(conn)
graph = StateGraph(ChatState)

#add nodes
graph.add_node("chat_node", chat_node)
graph.add_node("tool_node", tool_node)

graph.add_edge(START, "chat_node")
graph.add_conditional_edges("chat_node", tools_condition, {"tools": "tool_node", "__end__": END})
graph.add_edge("tool_node", "chat_node")

chatbot= graph.compile(checkpointer=checkpointer)

def retrive_all_threads():
    all_threads=set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config['configurable']['thread_id']) # pyright: ignore[reportTypedDictNotRequiredAccess]
    return list(all_threads)
