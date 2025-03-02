
from langchain_openai import ChatOpenAI
import asyncio  

async def task1():
    model = ChatOpenAI(
        model="deepseek-chat",
        base_url="https://api.deepseek.com/v1",
        api_key="sk-d61fcc515cc54ad1af8210b74eccfbd6",
        temperature=0.1,
    )
    chunks = []
    async for chunk in model.astream("天空是什么颜色"):
        chunks.append(chunk)
        if len(chunks)==2:
            print(chunks[1])
        print(chunk.content,end="|",flush=True)

async def task2():
    model = ChatOpenAI(
        model="deepseek-chat",
        base_url="https://api.deepseek.com/v1",
        api_key="sk-d61fcc515cc54ad1af8210b74eccfbd6",
        temperature=0.1,
    )
    chunks = []
    async for chunk in model.astream("讲个笑话"):
        chunks.append(chunk)
        if len(chunks)==2:
            print(chunks[1])
        print(chunk.content,end="|",flush=True)
        
async def main():
    await task1()
    await task2()   
    #异步说明，开发运行两个任务
    #await asyncio.gather(task1(),task2())

asyncio.run(main()) 