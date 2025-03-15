# 导入 Aps 工具
import aps_tools

# os
import os


import time


# langchain tools
from typing import Literal
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

# langgraph tools
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph, MessagesState
from langgraph.prebuilt import ToolNode
from IPython.display import Image, display



# rich 工具
from rich.console import Console

from rich.live import Live
from rich.text import Text
from rich.prompt import Prompt
from rich.panel import Panel
from rich.spinner import Spinner
import logging
import asyncio


console = Console()

logging.basicConfig(
    filename="aps_assistant.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)

# 将工具函数添加到工具列表
tools = [aps_tools.call_all_aps_data,
    aps_tools.count_all_cars_total_amounts,
    aps_tools.call_aps_data_for_specific_saling_model,
    aps_tools.call_all_saling_models_within_series,
]

# 创建工具节点
tool_node = ToolNode(tools=tools)


# 使用bind_tools方法将工具列表发送给模型，模型会视工具的 【描述部分】 自动调用工具，这就是function calling
# llm = ChatOpenAI(model_name="deepseek-chat",base_url='https://api.deepseek.com/v1',api_key='sk-d61fcc515cc54ad1af8210b74eccfbd6',temperature=0.1)
# llm = ChatOpenAI(
#     model_name="gpt",
#     temperature=0.1,
# )

model_series = "qwen"


def custom_sync_tool_node(state: MessagesState):
    logging.info("这里是同步节点开始")
    time.sleep(10)  # 模拟同步操作
    logging.info("同步节点结束")
    return None


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


# 定义一个路由函数，决定是否继续执行【条件边】
def should_continue(state: MessagesState) -> Literal["tools", END]:
    # 获取大模型的消息
    messages = state["messages"]

    last_message = messages[-1]

    # print("\n", ">" * 10, "判断是否调用function", "<" * 10)
    # print(f"判断状态:{last_message.tool_calls}")
    func_message = last_message.tool_calls

    if func_message:
        func_panel = Panel(
            str(func_message),
            title="Function Calling",
            style="white",
            border_style="bold white",
        )
        logging.info(func_message)
        console.print(func_panel)

    # 如果LLM调用了工具，则条传到“tools”节点
    if last_message.tool_calls:
        # 返回 “边” 的名字
        return "tools"

    # 否则停止
    return "end"


# 调用模型,并生成回复
def call_model(state: MessagesState):
    messages = state["messages"]
    logging.info("模型正在生成回答...")
    
    # stream output
    print('\n',">"*10,"模型回答",'<'*10)
    _text = ""
    with Live(Text(""),vertical_overflow='visible') as live:
        for _chunk in model.stream(messages):
            _text += str(_chunk.content)
            live.update(Text(_text,style="red"))
    response = model.invoke(messages)
    logging.info(f"模型回答：{response.content}")
    return {"messages": [response]}


# 用状态初始化图,定义一个新的状态图
async_tool_node = ToolNode(tools=tools)

# 用状态初始化图，定义一个新的状态图
workflow = StateGraph(MessagesState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", async_tool_node)
workflow.add_node("simple_node", custom_sync_tool_node)  # 添加自定义异步工具节点

# 添加入口和边
workflow.set_entry_point("agent")


# # 添加条件边
# workflow.add_conditional_edges("agent", should_continue,{"end": END,"tools": "tools"})

# 添加边
# workflow.add_edge("agent", "tools")
workflow.add_edge("agent", "simple_node")  # 将 agent 与 simple_node 连接

# 添加条件边
workflow.add_conditional_edges("simple_node", should_continue,{"end": END,"tools": "tools"})


# 初始化内存,以在图运行之间持久化状态
checkpointer = MemorySaver()


# 编译图
app = workflow.compile(checkpointer=checkpointer)
try:
    img_data = app.get_graph().draw_mermaid_png()
    with open("graph_image.png", "wb") as img_file:
        img_file.write(img_data)
except Exception as e:
    print(f"Error occurred: {e}")

# 执行图
def answer(question: str) -> str:
    """
    question: str - 用户的问题
    """
    logging.info(f"收到的用户数据：{question}")
    with console.status("[bold green]正在思考...[/bold green]", spinner="bouncingBar"):
        
        #记录开始时间
        
        start_time = time.time()
        
        final_state = app.invoke(
            {
                "messages": [
                    SystemMessage(
                        content="""
                        你是一个专业的汽车APS助手,擅长使用数据库工具,
                        并擅长基于工具返回的数据库进行精确且专业的数据分析,
                        为保证准确性,你每次回答问题的时候都需要调用工具,
                        并且在回答的时候告诉我你调用了什么工具,
                        你需要尽一切可能精确,不允许省略内容,并为用户生成专业的报告以回答用户的问题
                        """
                    ),
                    HumanMessage(content=question),
                ]
            },
            # thread_id 相同代表在同一个会话中
            config={"configurable": {"thread_id": 42}},
        )
        # print(final_state)
        result = "===================" + final_state["messages"][-1].content
        logging.info(f"最终回答：{result}")
        
        # 结束时间并计算持续时间
        end_time = time.time()
        elapsed_time = end_time - start_time
        logging.info(f"回答问题所用时间{elapsed_time:.2f}")
        panel = Panel(
            result,
            style="bright_green",
            expand=False,
            border_style="bold white",
            title="模型回答",
            title_align="center",
        )
        console.print(panel)


def main():
    """
    主函数
    """
    logging.info("程序启动")
    # 初次运行时清屏
    os.system("cls" if os.name == "nt" else "clear")
    while True:

        
        question = Prompt.ask("[bold green]请输入问题[/bold green]")
        user_input = question.strip()
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        else:
            #question = "你好"
            logging.info(f"用户输入:{question}")
            # 将输入的问题用Panel包裹起来并打印
            input_panel = Panel(
                question, title="问题", style="blue", border_style="bold white"
            )
            console.print(input_panel)
            answer(question)

if __name__ == "__main__":
    main()
# end
