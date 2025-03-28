from langchain_core.prompts import ChatPromptTemplate,MessagesPlaceholder
from langchain_openai.chat_models import ChatOpenAI
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables import RunnableWithMessageHistory
#创建一个聊天提示词模板
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "你是一个可以用于{task}的智能助手"
        ),
        #历史消息占位符
        MessagesPlaceholder(variable_name="history"),
     
        ("human","{input}")
    ]
)
model = ChatOpenAI(
        model="deepseek-chat",
        base_url="https://api.deepseek.com/v1",
        api_key="sk-d61fcc515cc54ad1af8210b74eccfbd6",
        temperature=0.1,
    )
runnable = prompt | model
#用来存储聊天历史，是一个字典类型
store = {}
#获取会话历史，入参是会话id，返回值是一个聊天历史
def get_session_history(session_id:str)->BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

with_message_history = RunnableWithMessageHistory(
    runnable,get_session_history,input_key="input",output_key="history"
)


response = with_message_history.invoke(
    input="你好",
    task="帮我润色文章内容",
    session_id="test"
)                   
