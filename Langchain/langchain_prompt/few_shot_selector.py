#挑选示例，对向量进行相似度匹配----》这个是一个小型的rag，也就是小型知识库，让ai可以学习一些简单的知识
from langchain.prompts.few_shot import FewShotPromptTemplate
from langchain.prompts.prompt import PromptTemplate 
#小型的rag,也就是小型知识库，让ai可以学习一些简单的知识
examples = [
    {
        "question":"你是谁",
        "answer":"我是一个智能助手" 
    },
    {
        "question":"你是什么",
        "answer":"我是一个助手"
    }

]

from langchain.prompts.example_selector import SemanticSimilarityExampleSelector
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
#这里由于我们不能调用openai的api，所以这个代码跑不通，看明白就行
examlpes_selector = SemanticSimilarityExampleSelector.from_examples(
    examples,
    OpenAIEmbeddings(),
    Chroma(),
    K=1
)

question = "请问你是谁"
selected_example = examlpes_selector.select_example({"question":question})
print(f"最相似的示例：{question}")
for example in selected_example:
    print("\\n")
    for k,v in example.items():
        print(f"{k}:{v}")
