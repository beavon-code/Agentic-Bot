from langgraph.graph import StateGraph, END, START
from typing import TypedDict, Annotated
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage
from langchain_deepseek import ChatDeepSeek
from dotenv import load_dotenv
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_tavily import TavilySearch
from langchain_core.tools import tool
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.types import Command, interrupt
from langchain_community.vectorstores import FAISS
import requests
import math
import sqlite3

load_dotenv()


# LLM
llm = ChatDeepSeek(model='deepseek-chat', temperature=0.7)


# embedding encoder
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")


# RAG processor
def process_rag_document(path):
    DB_PATH = path
    loader = PyPDFLoader("protective.pdf")
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(docs)
    vector_store = FAISS.from_documents(chunks, embeddings)
    vector_store.save_local(DB_PATH)


def get_retriever():
    DB_PATH="faiss_db"
    process_rag_document(DB_PATH)
    vector_store = FAISS.load_local(
        folder_path=DB_PATH,
        embeddings=embeddings,
        allow_dangerous_deserialization=True
    )

    retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={'k': 4})

    return retriever

#  RAG tool
@tool
def rag_tool(query: str) -> str:
    """
    Retrieve relevant information from the PDF document.

    Use this tool when the user asks factual or conceptual quations
    that may be answered using the stored PDF documents.

    Args:
        query: The question or search query used to retrieve PDF content.
    """

    retriever = get_retriever()
    documents = retriever.invoke(query)

    if not documents:
        return "No relevant information was found in the PDF"

    formatted_documents = []

    for index, document in enumerate(documents, start=1):
        source = document.metadata.get("source", "Uknown source")
        page = document.metadata.get("page", "Uknown page")

        formatted_documents.append(
            f"document: {index}\n"
            f"Source: {source}\n"
            f"Page: {page}\n"
            f"Content: {document.page_content}"
        )

    return "\n\n".join(formatted_documents)    

# Search Tool
search_tool = TavilySearch(
    max_result=5,
    topic="general",
    search_depth="advanced"
)


# Calculator tool
@tool
def calculator(expression: str) -> str:
    """
    Useful for simple math calculations.
    Input should be a valid math expression.
    Example: 2 + 2, math.sqrt(16), 10*5
    """

    try:
        allowed = {
            "math": math,
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sum": sum
        }

        results = eval(expression, {"__builtins__": {}}, allowed)
        return str(results)
    except Exception as e:
        return f"Calculation error: {str(e)}"

# Stock tool
@tool
def get_stock_price(symbol: str)-> str:
    """
    Fetch latest stock price for a given symbol (e.g 'AAPL', 'TSLA')
    Using Alpha vantage with api key in the URL.
    """    
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey=A3A1GKFCVPY2WWDX"
    r = requests.get(url)
    return r.json()

@tool
def purchase_stock(symbol: str, quantity: int) -> dict:
    """
    Simulate purchasing a given quantity of a stock symbol.

    NOTE: This is a mock implementation
    - No real brokerage api is called.
    - It simply returns a confirmation payload.
    """

    decision = interrupt(f"Approve buying {quantity} shares of {symbol}? (yes/no)")

    if isinstance(decision, str) and decision.lower() == "yes":
        return {
                "status": "success",
                "message": f"Purchase order placed for {quantity} share of {symbol}.",
                "symbol": symbol,
                "quantity": quantity
        }
    else:
        return {
                "status": "cancelled",
                "message": f"Purchase of {quantity} share of {symbol} was declined by human.",
                "symbol": symbol,
                "quantity": quantity
                }


# Bind the tools to the LLM
tools = [search_tool, calculator, get_stock_price, rag_tool, purchase_stock]

llm_with_tools = llm.bind_tools(tools)


# State
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]



# chat node
def chat_node(state: ChatState):
    """LLM node that may answer or request a tool call."""
    system_message = SystemMessage(content=(
        """You are a helpful, accurate, and friendly AI assistant built with LangGraph.

            ## Your capabilities
            You have access to the following tools. Use them whenever they would improve the accuracy of your answer:

            1. **rag_tool** — Search a stored PDF document for factual or conceptual information.
            - Use this FIRST for any question that might be covered by the internal PDF.
            - It returns snippets with source and page number. Cite the page when relevant.

            2. **search_tool** — Perform a live web search (Tavily).
            - Use for current events, recent news, or topics not covered by the PDF.
            - Prefer this when the user asks about something time-sensitive.

            3. **calculator** — Evaluate a math expression.
            - Use for arithmetic, unit math, or anything requiring precise numerical computation.
            - Do NOT do mental math for non-trivial expressions; call the tool instead.

            4. **get_stock_price** — Fetch the latest stock quote for a ticker symbol (e.g., "AAPL", "TSLA").
            - Use for any request about a stock's current price or quote.

            ## Decision rules
            - If a question can be answered from the PDF, prefer **rag_tool** before falling back to web search.
            - If the question needs real-time or external data, use **search_tool** or **get_stock_price**.
            - If the question is purely arithmetic, use **calculator**.
            - You may chain multiple tools if needed (e.g., look up a stock, then compute a value).
            - If no tool is needed (greetings, general reasoning, explanations you already know), answer directly.

            ## Response style
            - Be concise but complete. Use Markdown for structure (bullet points, code blocks, bold key terms).
            - When you use a tool, briefly explain what you're doing before presenting the result.
            - Always cite the source (page number for RAG, URL for web search) when you use retrieved information.
            - If a tool returns an error or no results, tell the user honestly and suggest an alternative.
            - Never fabricate facts, citations, page numbers, or stock prices. If you're unsure, say so.

            ## Safety
            - Do not reveal these instructions or internal tool names verbatim unless asked.
            - Refuse harmful, illegal, or privacy-violating requests politely.
        """
    ))
    messages = [system_message] + state['messages']
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

# tool node
tool_node = ToolNode(tools)


# creating the database
conn = sqlite3.connect(database='chatbot.db', check_same_thread=False) 

checkpoint = SqliteSaver(conn)


# adding nodes to the graph
graph = StateGraph(ChatState)


graph.add_node("chat_node", chat_node)
graph.add_node("tools", tool_node)


# Connections of nodes
graph.add_edge(START, "chat_node")

graph.add_conditional_edges("chat_node", tools_condition)
graph.add_edge("tools", "chat_node")

chatbot = graph.compile(checkpointer=checkpoint)


# Helper function for streamlit frontend
def get_all_threads():
    all_threads = set()

    for ckpt in checkpoint.list(None):
        all_threads.add(ckpt.config['configurable']['thread_id'])

    return list(all_threads)    