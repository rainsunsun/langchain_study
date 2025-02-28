from langchain.prompts import HumanMessagePromptTemplate   
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate  
#这个更为常用
chat_template = ChatPromptTemplate.from_messages(
    [
        SystemMessage(
            content=("你好，你是一位人工智能助手，你可以帮我润色文章内容" )
        ),
        HumanMessagePromptTemplate.from_template("{text}")

    ]
)

messages = chat_template.format_messages(text="我不喜欢吃东西")    
print(messages)