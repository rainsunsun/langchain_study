from langchain_openai import ChatOpenAI 
import asyncio
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_template("{topic}是什么颜色")
model = ChatOpenAI(
        model="deepseek-chat",
        base_url="https://api.deepseek.com/v1",
        api_key="sk-d61fcc515cc54ad1af8210b74eccfbd6",
        temperature=0.1,
    )
parser = StrOutputParser()
chain = prompt | model | parser     

async def async_stream():
    async for chunk in chain.astream({"topic": "天空"}):
        print(chunk,end="|",flush=True)
#运行异步流处理
asyncio.run(async_stream())