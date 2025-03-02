
from langchain_openai import ChatOpenAI
#这里的代码API调用用的是qjr的
model = ChatOpenAI(
        model="deepseek-chat",
        base_url="https://api.deepseek.com/v1",
        api_key="sk-d61fcc515cc54ad1af8210b74eccfbd6",
        temperature=0.1,
    )
chunks = []
for chunk in model.stream("天空是什么颜色"):
      chunks.append(chunk)
      print(chunk.content,end="|",flush=True)
      
          