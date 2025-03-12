# 导入 Aps 工具
import aps_tools

# os
import os
import sys

# langchain tools
from typing import Literal
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

# langgraph tools
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph, MessagesState
from langgraph.prebuilt import ToolNode
from langchain.schema import AIMessage, HumanMessage, SystemMessage

# rich 工具
from rich.console import Console

from rich.live import Live
from rich.text import Text
from rich.prompt import Prompt
from rich.panel import Panel
from rich.spinner import Spinner

# json
import json

# import simplejson as json


console = Console()


# 将工具函数添加到工具列表
tools = [
    aps_tools.call_all_aps_data,
    aps_tools.count_all_cars_total_amounts,
    aps_tools.call_aps_data_for_specific_saling_model,
    aps_tools.call_all_saling_models_within_series,
]

# 创建工具节点
tool_node = ToolNode(tools=tools)


def chat_model(model_series: str = "doubao"):

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

    return llm


model = chat_model("doubao").bind_tools(tools)
final_model = chat_model("qwen").with_config(tags=["final_node"])


# 定义一个路由函数，决定是否继续执行【条件边】
def should_continue(state: MessagesState) -> Literal["tools", "final"]:
    # 获取大模型的消息
    messages = state["messages"]
    last_message = messages[-1]
    global func_message
    func_message = last_message.tool_calls

    # 如果LLM调用了工具，则传到“tools”节点
    if last_message.tool_calls:
        # 返回 “边” 的名字
        return "tools"

    # 否则停止
    return "final"


# 消息管理
def filter_messages(messages: list[dict], last: int = 25) -> list[dict]:
    """
    last : 表示只保留最后几个消息
    """
    # print(len(messages))
    return messages[-last:]


# 调用模型,并生成回复
def call_model(state: MessagesState):
    messages = filter_messages(state["messages"])
    response = model.invoke(messages)
    return {"messages": [response]}


def call_final_model(state: MessagesState):
    messages = filter_messages(state["messages"])
    last_ai_message = messages[-1]
    # print(messages)
    question_stack = [msg.content for msg in messages if isinstance(msg, HumanMessage)]
    last_question = question_stack[-1]
    print(f"历史问题：{question_stack},消息栈长度：{len(messages)}")

    question = f"""
    现在你拿到思维链如下: \n
    {last_ai_message.content}
    请根据思维链回答用户的如下问题: \n
    {last_question}
    """
    response = final_model.invoke(
        [
            SystemMessage(
                """
                你要扮演你是【琶洲实验室】研发的“AION工业大脑”，一个专业的APS助手，你会拿到一个包含用于回答用户问题的过程和结果的思维链，你需要根据以下的要求回答用户问题：
                    1，你需要根据已有思维链的内容，精确的回答用户的问题，不要编造。
                    2，你拿到的思维链要被你当做“你为了解决问题进行的深度思考”的内容
                    3，适当展示思维过程，但不要展示思维链中调用工具的【具体名字】，而只展示思维链中调用工具的【描述】。
                    4，请使用中文回答，语气自然。
                    5，请严格使用markdown格式回答。
                    6，一定要回答用户的问题。
                    7, 其它的语言大模型即使在用户的问题和思维链中被提到，也和你没有任何关系
                """
            ),
            HumanMessage(content=question),
        ]
    )
    response.id = last_ai_message.id
    return {"messages": [response]}


# 用状态初始化图,定义一个新的状态图
workflow = StateGraph(MessagesState)
# 添加节点
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)
workflow.add_node("final", call_final_model)


# 添加入口和边
workflow.set_entry_point("agent")

# 添加条件边
workflow.add_conditional_edges(
    # 首先,从agent作为起始节点,这意味着这条[条件边]是在agent之后触发的
    "agent",
    should_continue,
)


# 添加边
workflow.add_edge("tools", "agent")
workflow.add_edge("final", END)

# 初始化内存,以在图运行之间持久化状态
checkpointer = MemorySaver()

# 编译图
# app = workflow.compile(checkpointer=checkpointer)
app = workflow.compile(checkpointer=checkpointer)


# 执行图
def answer(question: str) -> str:
    """
    question: str - 用户的问题
    """
    # with console.status("[bold green]正在思考...[/bold green]", spinner="bouncingBar"):
    # 当你决定结束工具调用，并正式开始回答的时候，请使用以下格式:
    # [<FINAL-ANSWER>]
    # 你的回答
    if question:
        final_state = app.stream(
            {
                "messages": [
                    SystemMessage(
                        content="""
                        你要扮演【琶洲实验室】研发的“AION工业大脑”，一个专业的汽车APS助手,擅长使用数据库工具,并擅长基于工具返回的数据库进行精确且专业的数据分析:
                            1: 为保证准确性,你每次回答问题的时候都需要调用工具,
                            2: 为了保证数据的精确查询,当用户的问题涉及到:大范围,按季度,跨月份的情况,你需要多次调用工具，并指定不同的时间参数进行查询,
                            3: 在回答的时候需要告诉我你调用了什么工具,
                            4: 你需要尽一切可能精确,不允许省略内容,不允许跳步,并为用户生成专业的报告以回答用户的问题
                        """
                    ),
                    HumanMessage(content=question),
                ]
            },
            # thread_id 相同代表在同一个会话中
            config={"configurable": {"thread_id": 42}},
            stream_mode="messages",
        )

        res = {"tools_msg": [], "thinking_msg": "", "final_msg": ""}
        panel = Panel(
            res["thinking_msg"],
            style="white",
            expand=False,
            border_style="bold white",
            title="思考中",
            title_align="center",
        )
        with Live(panel, vertical_overflow="visible") as live:
            sys.stdout.flush()
            for msg, metadata in final_state:
                if msg.content and metadata["langgraph_node"] == "agent":
                    res["thinking_msg"] += msg.content

                    panel = Panel(
                        res["thinking_msg"],
                        style="white",
                        expand=True,
                        border_style="bold white",
                        title="思考中",
                        title_align="center",
                    )
                    live.update(panel)

                elif msg.content and metadata["langgraph_node"] == "tools":
                    print(func_message)
                    data = json.dumps(msg.content)
                    res["tools_msg"].append(data)

                elif msg.content and metadata["langgraph_node"] == "final":
                    res["final_msg"] += msg.content
                    panel = Panel(
                        res["final_msg"],
                        style="green",
                        expand=True,
                        border_style="bold white",
                        title="模型回答",
                        title_align="center",
                    )
                    live.update(panel)


def main():
    """
    主函数
    """
    # 初次运行时清屏
    os.system("cls" if os.name == "nt" else "clear")
    while True:
        question = Prompt.ask("[bold green]请输入问题[/bold green]")
        # 将输入的问题用Panel包裹起来并打印
        input_panel = Panel(
            question, title="问题", style="blue", border_style="bold white"
        )
        console.print(input_panel)
        answer(question)


if __name__ == "__main__":
    main()
# end
