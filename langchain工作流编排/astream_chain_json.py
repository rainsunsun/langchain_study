from langchain_openai import ChatOpenAI 
import asyncio
from langchain_core.output_parsers import StrOutputParser
from langchain_core.output_parsers import JsonOutputParser

model = ChatOpenAI(
        model="deepseek-chat",
        base_url="https://api.deepseek.com/v1",
        api_key="sk-d61fcc515cc54ad1af8210b74eccfbd6",
        temperature=0.1,
    )
chain = model | JsonOutputParser() 

async def async_astream():
    async for text in chain.astream(
        "以json格式输出法国,西班牙的人口数量列表,并且是中文格式"
        "使用一个带有'countries'外部键的字典，其中包含国家列表。"
        "每个国家都应该有name和population键。"
        ):
        print(text,end="|",flush=True)
asyncio.run(async_astream())