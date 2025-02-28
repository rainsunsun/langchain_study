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

example_prompt = PromptTemplate(input_variables=["question","answer"],template="问题：{question} \\n{answer}")
prompt = FewShotPromptTemplate(
    examples=examples,
    example_prompt=example_prompt,
    suffix="问题：{input}",
    input_variables=["input"]   
)
                                
print(prompt.format(input="你是谁"))                       