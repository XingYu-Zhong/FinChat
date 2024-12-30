import openai
import time

class OpenaiApi:
    def __init__(self, api_key, base_url="",model = 'gpt-4o-2024-08-06'):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

        self.client = openai.OpenAI(api_key=self.api_key,base_url=self.base_url) if base_url!="" else openai.OpenAI(api_key=self.api_key)
    def stream_chat_model(self, messages_list, model=None, temperature=0.2, top_p=0.95):
        model = model if model else self.model
        stream = self.client.chat.completions.create(
            model=model,
            messages=messages_list,
            temperature=temperature,
            top_p=top_p,
            stream=True  # 启用流式输出
        )
        return stream
    

    def chat_model(self, messages_list, model=None, temperature=0.2, top_p=0.95):
        model = model if model else self.model
        
        try:
            # 记录输入的消息
            # print(f"Input messages: {messages_list[0]['content']}")
            
            resp = self.client.chat.completions.create(
                model=model,
                messages=messages_list,
                temperature=temperature,
                top_p=top_p,
            )
            content = resp.choices[0].message.content
            
            # 记录输出的响应
            # print(f"Output response: {content}")
            
            # 可以选择将日志写入文件
            with open('chat_logs.txt', 'a', encoding='utf-8') as f:
                f.write(f"\n--- {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
                f.write(f"Model: {model}\n")
                f.write(f"Input: {str(messages_list[0]['content'])}\n")
                f.write(f"Output: {content}\n")
                f.write("-" * 50 + "\n")
            
            return content
        
        except Exception as e:
            # 记录错误信息
            error_msg = f"An error occurred: {e}. Retrying in 1 minute...model:{model}"
            print(error_msg)
            with open('chat_logs.txt', 'a', encoding='utf-8') as f:
                f.write(f"\n--- {time.strftime('%Y-%m-%d %H:%M:%S')} ERROR ---\n")
                f.write(f"{error_msg}\n")
            
            time.sleep(60)  # Wait for 1 minute before retrying
            return self.chat_model(messages_list, model=model, temperature=temperature, top_p=top_p)

    def embedding_model(self,text,model = "text-embedding-ada-002"):
        if len(text) > 5120:
            text = text[:5120]
        max_retries = 50
        retries = 0
        while retries < max_retries:
            try:
                response = self.client.embeddings.create(
                    model=model,
                    input=text
                )
                break
            except Exception as e:
                print(f"An error occurred: {e},query:{text}")
                retries += 1
                if retries >= max_retries:
                    raise e
                time.sleep(60)  # Optional: wait for 2 seconds before retrying
        return response.data[0].embedding