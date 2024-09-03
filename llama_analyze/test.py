import os
from together import Together
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 初始化 Together 客户端
together_client = Together(api_key=os.environ.get('TOGETHER_API_KEY'))

# 创建测试函数
def test_together_api():
    # 创建一个简单的消息用于测试
    message = {
        'role': 'user',
        'content': 'Tell me a joke.'
    }

    try:
        # 调用 Together AI API
        response = together_client.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
            messages=[message],
            max_tokens=100,
            temperature=0.7,
            top_p=0.7,
            top_k=50,
            repetition_penalty=1,
            stop=["<|eot_id|>", "<|eom_id|>"],
            stream=True  # 使用流式输出
        )

        # 初始化变量以累积生成的内容
        accumulated_text = ""

        # 遍历响应并检查每个部分的属性
        for part in response:
            if hasattr(part, 'choices'):
                for choice in part.choices:
                    if hasattr(choice, 'delta'):
                        # 累积 delta.content 的内容
                        accumulated_text += choice.delta.content

        # 输出完整的累积文本内容
        print("Generated content:", accumulated_text)

    except Exception as e:
        print("Error during API call:", str(e))

# 运行测试
if __name__ == "__main__":
    test_together_api()
