from langchain_openai import ChatOpenAI
import asyncio  
model = ChatOpenAI(
        model="deepseek-chat",
        base_url="https://api.deepseek.com/v1",
        api_key="sk-d61fcc515cc54ad1af8210b74eccfbd6",
        temperature=0.1,
    )
async def async_stream():
    events=[]
    async for event in model.astream("hello"):#删除了v2是因为对于deepseek—chat模型来说，v2是不需要的
        events.append(event)
        print(event.content,end="|",flush=True)
    print(events)
asyncio.run(async_stream())