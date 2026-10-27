from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
import os

def get_llm():
    return ChatGroq(model = "openai/gpt-oss-20b", groq_api_key = os.getenv("GROQ_API_KEY"), temperature = 0.3)

def split_transcript(transcript: str) -> list:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=3000,
        chunk_overlap=200
    )
    return splitter.split_text(transcript)

def summarize(transcript: str) -> str:
    llm = get_llm()
    map_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that summarizes transcripts of videos. Summarize the following transcript in a concise manner, highlighting the key points and main ideas. Ensure that the summary is clear and easy to understand."),
        ("user", "Transcript: {text}")
    ])

    map_chain = map_prompt | llm | StrOutputParser()

    chunks = split_transcript(transcript)
    chunk_summaries = [map_chain.invoke({"text": chunk}) for chunk in chunks]
    combined_summary = " ".join(chunk_summaries)

    combined_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert summarizer. Combine these partial summaries into a single professional summary in bullet points."),
        ("user", "{text}")
    ])

    combined_chain = (
        RunnablePassthrough() | RunnableLambda(lambda x: {"text": x}) | combined_prompt | llm | StrOutputParser()
    )
    final_summary = combined_chain.invoke(combined_summary)
    return final_summary

def generate_title(transcript: str) -> str:
    llm = get_llm()
    title_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a creative assistant that generates titles for video transcripts. Create a catchy and relevant title based on the content of the transcript."),
        ("user", "Transcript: {text}")
    ])

    title_chain = title_prompt | llm | StrOutputParser()
    title = title_chain.invoke({"text": transcript[:2000]})
    return title