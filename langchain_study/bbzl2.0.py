
# 导入必要的库
import calendar
import dateutil.parser as parser
from datetime import date
from langchain.tools import Tool, tool
from langchain.agents import create_react_agent
from langchain.agents import AgentExecutor
from langchain_openai import ChatOpenAI
from langchain import hub
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from typing import Literal
from langgraph.prebuilt import ToolNode
from langgraph.graph import END, StateGraph, MessagesState
from langgraph.checkpoint.memory import MemorySaver

# ---------------- 工具定义 ----------------
@tool("weekday")
def weekday(date_str: str) -> str:
    """Convert date to weekday name"""
    d = parser.parse(date_str)
    return calendar.day_name[d.weekday()]

tools = [weekday]  # 将自定义的 tool 添加到 tools 数组中
tool_node = ToolNode(tools)

# ---------------- 模型配置 ----------------
# 优化模型：
model_series = "qwen"

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

# ---------------- 图构建相关函数定义 ----------------
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
class State(TypedDict):
    messages:Annotated[list,add_messages]


def should_continue(state:State) -> Literal["tools", END]:
    messages = state['messages']
    last_message = messages[-1]
    # 如果LLM调用了工具，则转到“tools”节点
    if last_message.tool_calls:
        return "tools"
    # 否则，停止（回复用户）
    return END

# 定义调用模型的函数
def call_model(state: State):
    messages = state['messages']
    response = model.invoke(messages)
    # 返回列表，因为这将被添加到现有列表中
    return {"messages": [response]}

# ---------------- 状态图构建 ----------------
# 用状态初始化图，定义一个新的状态图
workflow = StateGraph(State)
# 定义图节点，定义我们将循环的两个节点
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)
# 定义入口点和图边
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
memory = MemorySaver()

# 编译图
# 这将其编译成一个LangChain可运行对象，
# 这意味着你可以像使用其他可运行对象一样使用它。
# 注意，我们（可选地）在编译图时传递内存
app = workflow.compile(checkpointer=memory)

# ---------------- 提示词模板定义 ----------------
# 定义系统消息
system_message = SystemMessagePromptTemplate.from_template(
    "你是一个搜索日期的智能机器人xsun。必须使用提供的工具来回答问题。"
)

# 定义工具描述
tools_description = """
你有以下工具可用：
{tools}
"""

# 定义用户消息模板
human_template = """
Answer the following questions as best you can. Use the following format:
Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action，如果其中有日期，请确保只输入日期，格式为:YYYY-MM-DD，不要有任何其它字符
Observation: the result of the action，如果其中有日期，请确保输出的日期格式为:YYYY-MM-DD，不要有任何其它字符
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin! Let's think step by step. Take a deep breath.

Question: {input}
Thought:{agent_scratchpad}
"""

# 组合提示词模板
prompt = ChatPromptTemplate.from_messages([
    system_message,
    SystemMessagePromptTemplate.from_template(tools_description),
    HumanMessagePromptTemplate.from_template(human_template)
])


# ---------------- 图绘制 ----------------
# 开始画图
graph_png = app.get_graph().draw_mermaid_png()
with open("langgraph_bbzl.png", "wb") as f:
    f.write(graph_png)


# ---------------- Agent 创建和调用 ----------------

config = {"configurable": {"thread_id": "1"}}

agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# 执行图
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.messages import HumanMessage, SystemMessage
def answer(question: str) -> str:
    """
    question: str - 用户的问题
    """
    
    final_state = app.invoke(
            {
                "messages": [
                    SystemMessage(
                        content="""
                        你是一个搜索日期的智能机器人xsun。必须使用提供的工具来回答问题,
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
    print(result)
        

    
from rich.prompt import Prompt

def main():
    """
    主函数
    """
    
    while True:

        question = Prompt.ask("[bold green]请输入问题[/bold green]")
        user_input = question.strip()
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        else:
            #question = "你好"
            answer(question)

if __name__ == "__main__":
    main()
# end



            
            