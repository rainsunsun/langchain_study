#导入langchain提示词模板库
from langchain_core.prompts import ChatPromptTemplate

chat_template = ChatPromptTemplate.from_messages(
    [
        ("system", "你好，你是一位人工智能助手，你的名字是{name},"),
        ("human", "你好"),
        ("ai","我很好，谢谢！"),
        ("human","{user_input}")
    ]  
)

#通过模板参数格式化模板内容
messages = chat_template.format_messages(name="Bob",user_input="你的名字叫什么")
print(messages)