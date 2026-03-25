import openai
import time

# 1. 初始化客户端，指向本地 LM Studio
client = openai.OpenAI(
    base_url="http://localhost:1234/v1",
    api_key="lm-studio-local"
)

# 2. 构造给 FunSearch 变异算子的测试提示词
test_prompt = """
We are solving the online bin packing problem.
Please write a Python heuristic function `def heuristic(bins, item):` that scores how well an item fits into a bin.
Make it clever, combining both the residual capacity and a non-linear penalty for fragmentation.
Output ONLY the python code without any markdown formatting or explanations.
"""

def test_qwen_coder():
    print("\n🚀 开始测试: [Qwen3 Coder 纯净输出与速度测试] ...")
    
    # 纯净代码生成配置
    kwargs = {
        "model": "qwen3-coder-local", # LM Studio 会自动映射给当前加载的模型
        "messages": [
            # 强化系统提示，逼迫它像一个无情的代码接口
            {"role": "system", "content": "You are a pure code generator. Output ONLY valid Python code starting exactly with 'def'. Do not use markdown blocks like ```python. Do not explain."},
            {"role": "user", "content": test_prompt}
        ],
        "temperature": 0.2, # 降低温度，提高代码稳定性
        "max_tokens": 1024,
    }

    start_time = time.time()
    try:
        response = client.chat.completions.create(**kwargs)
        # strip() 去掉可能存在的前后空格和换行
        result = response.choices[0].message.content.strip() 
        elapsed_time = time.time() - start_time
        
        print("-" * 50)
        print("🤖 模型的原始输出开头 (前 200 个字符)：\n")
        print(result[:200] + "\n...\n") 
        print("-" * 50)
        
        # 自动检测逻辑（不仅查思考，还查有没有 Markdown 代码块包裹）
        if "<think>" in result or "Thinking" in result or "```" in result:
            print(f"❌ 测试失败：模型依然输出了废话或 Markdown 格式。耗时: {elapsed_time:.2f} 秒")
        elif result.startswith("def "):
            print(f"✅ 测试大成功！没有任何废话，直接输出了纯净代码！耗时: {elapsed_time:.2f} 秒")
            print("🎉 你的 FunSearch 变异引擎现在可以满血全速开跑了！")
        else:
            print(f"⚠️ 勉强及格：没有废话，但开头不是 'def'。可能多输出了 import。耗时: {elapsed_time:.2f} 秒")
            
    except Exception as e:
        print(f"❌ 请求发生错误: {e}")

# ==========================================
# 执行测试
# ==========================================
print("=== Qwen3 Coder 30B (MoE) 极限速度与纯净度测试 ===")
test_qwen_coder()
