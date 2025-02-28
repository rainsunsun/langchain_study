from langchain_core.prompts import ChatPromptTemplate,MessagesPlaceholder
from langchain_core.messages import HumanMessage,SystemMessage

prompt_template = ChatPromptTemplate.from_messages([
    (
        "system","你是一个智能助手"
    ),
    MessagesPlaceholder("msgs")
])

result = prompt_template.invoke({"msgs":[HumanMessage(content="hi!"),HumanMessage(content="你好") ]})
print(result)