import logging
from typing import Literal
from langchain_core.messages import HumanMessage

from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph, MessagesState
from langgraph.prebuilt import ToolNode
import aps_tools

logging.basicConfig(
    filename="aps_assistant.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)

# 定义工具函数，用于代理调用外部工具
tools = [
    aps_tools.call_all_aps_data,
    aps_tools.count_all_cars_total_amounts,
    aps_tools.call_aps_data_for_specific_saling_model,
    aps_tools.call_all_saling_models_within_series,
]

# 创建工具节点
tool_node = ToolNode(tools=tools)
model_series = "qwen"

def custom_sync_tool_node(state: MessagesState):
    logging.info("这里是同步节点开始")
    import time
    time.sleep(10)  # 模拟同步操作
    logging.info("同步节点结束")
    return None

# 1. 初始化模型和工具，定义并绑定工具到模型
if model_series == "qwen":
    llm = ChatOpenAI(
        model="qwen-max",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key="sk-0ac182056fcd4a3eb1a883e453e0976d",
        temperature=0.01,
    )
elif model_series == "deepseek":
    llm = ChatOpenAI(
        model="deepseek-chat",
        base_url="https://api.deepseek.com/v1",
        api_key="sk-d61fcc515cc54ad1af8210b74eccfbd6",
        temperature=0.1,
    )
elif model_series == "doubao":
    llm = ChatOpenAI(
        model="ep-20250209190728-xzmmk",
        base_url="https://ark.cn-beijing.volces.com/api/v3/",
        api_key="da677bb3-2da7-4217-963b-90b324875011",
        temperature=0.1,
    )
else:
    raise ValueError("未指定模型")

model = llm.bind_tools(tools)

# 定义函数，决定是否继续执行
def should_continue(state: MessagesState) -> Literal["tools", END]:
    messages = state['messages']
    last_message = messages[-1]
    # 如果LLM调用了工具，则转到“tools”节点
    if last_message.tool_calls:
        return "tools"
    # 否则，停止（回复用户）
    return END

# 定义调用模型的函数
def call_model(state: MessagesState):
    try:
        messages = state['messages']
        response = model.invoke(messages)
        # 返回列表，因为这将被添加到现有列表中
        return {"messages": [response]}
    except Exception as e:
        logging.error(f"调用模型时出错: {e}，输入的消息: {messages}")
        raise

# 2. 用状态初始化图，定义一个新的状态图
workflow = StateGraph(MessagesState)
# 3. 定义图节点，定义我们将循环的两个节点
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)

# 4. 定义入口点和图边
# 设置入口点为“agent”
# 这意味着这是第一个被调用的节点
workflow.set_entry_point("agent")

# 添加条件边
workflow.add_conditional_edges(
    # 首先，定义起始节点。我们使用`agent`。
    # 这意味着这些边是在调用`agent`节点后采取的。
    "agent",
    # 接下来，传递决定下一个调用节点的函数。
    should_continue,
)

# 添加从`tools`到`agent`的普通边。
# 这意味着在调用`tools`后，接下来调用`agent`节点。
workflow.add_edge("tools", 'agent')

# 初始化内存以在图运行之间持久化状态
checkpointer = MemorySaver()

# 5. 编译图
# 这将其编译成一个LangChain可运行对象，
# 这意味着你可以像使用其他可运行对象一样使用它。
# 注意，我们（可选地）在编译图时传递内存
app = workflow.compile(checkpointer=checkpointer)

try:
    img_data = app.get_graph().draw_mermaid_png()
    with open("graph_image.png", "wb") as img_file:
        img_file.write(img_data)
except Exception as e:
    print(f"Error occurred: {e}")
# 6. 执行图，使用可运行对象
def answer(question: str) -> str:
    """
    question: str - 用户的问题
    """
    try:
        final_state = app.invoke(
            {"messages": [HumanMessage(content=question)]},
            config={"configurable": {"thread_id": 42}}
        )
        # 从 final_state 中获取最后一条消息的内容
        result = final_state["messages"][-1].content
        return result
    except Exception as e:
        logging.error(f"Error occurred during graph streaming: {e}，问题: {question}")
        print(f"Error occurred during graph streaming: {e}")
        return "Error occurred during graph streaming"

# 测试
question = "上海的天气怎么样?"
response = answer(question)
print(response)

question = "我问的那个城市?"
response = answer(question)
print(response)