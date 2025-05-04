import queue
import threading
import json
import time
import requests
import os
from dotenv import load_dotenv

# Ortam değişkenlerini yükle
load_dotenv()
API_KEY = os.getenv("AI_API_KEY")

# MACP mesaj kuyruğu
message_queue = queue.Queue()

# Developer Agent
class DeveloperAgent:
    def __init__(self, name):
        self.name = name
        self.api_key = API_KEY
        self.api_url = "https://api.openai.com/v1/chat/completions"

    def generate_code(self):
        # ChatGPT API'sine istek göndererek kod üret
        prompt = """Write a valid Python function named 'compute' that takes two numbers as input and returns their sum. 
        The function should be syntactically correct and executable. 
        Only return the function code, nothing else. Do not include any markdown code block markers."""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-3.5-turbo-0125",
            "messages": [
                {"role": "system", "content": "You are a helpful Python code generator. Return only valid Python code without any markdown formatting."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 200,
            "temperature": 0.7
        }
        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            code = result["choices"][0]["message"]["content"].strip()
            
            # Markdown code block işaretlerini temizle
            code = code.replace("```python", "").replace("```", "").strip()
            
            print(f"\n{self.name} tarafından üretilen kod:")
            print("----------------------------------------")
            print(code)
            print("----------------------------------------")
            return code
        except Exception as e:
            print(f"API hatası: {str(e)}")
            if hasattr(e, 'response'):
                print("API yanıtı:", e.response.text)
            return "def compute(a, b):\n    return a + b"  # Hata durumunda yedek kod

    def run(self):
        while True:
            if not message_queue.empty():
                msg = message_queue.get()
                if msg["type"] == "request" and msg["recipient"] == self.name:
                    print(f"{self.name} yeni kod üretiyor...")
                    code = self.generate_code()
                    message_queue.put({
                        "sender": self.name,
                        "recipient": "tester",
                        "type": "code",
                        "content": code
                    })
            time.sleep(1)

# Testçi Agent
class TesterAgent:
    def __init__(self, name):
        self.name = name

    def test_code(self, code):
        try:
            print(f"\n{self.name} kodu test ediyor...")
            print("Test edilen kod:")
            print("----------------------------------------")
            print(code)
            print("----------------------------------------")
            
            local_scope = {}
            exec(code, {}, local_scope)
            
            if "compute" not in local_scope:
                return {"status": "error", "message": "Kodda 'compute' fonksiyonu bulunamadı!"}
                
            compute = local_scope["compute"]
            result = compute(2, 3)
            return {"status": "success", "result": result, "message": "Kod başarıyla çalıştı!"}
        except SyntaxError as e:
            return {"status": "error", "message": f"Sözdizimi hatası: {str(e)}"}
        except Exception as e:
            return {"status": "error", "message": f"Çalışma hatası: {str(e)}"}

    def run(self):
        while True:
            if not message_queue.empty():
                msg = message_queue.get()
                if msg["type"] == "code" and msg["recipient"] == self.name:
                    print(f"{self.name} kodu test ediyor...")
                    result = self.test_code(msg["content"])
                    print(f"Test sonucu: {result}")
                    message_queue.put({
                        "sender": self.name,
                        "recipient": "developer",
                        "type": "feedback",
                        "content": result
                    })
                    message_queue.put({
                        "sender": self.name,
                        "recipient": "developer",
                        "type": "request",
                        "content": "Yeni kod gönder"
                    })
            time.sleep(1)

# Ajanları başlat
def main():
    developer = DeveloperAgent("developer")
    tester = TesterAgent("tester")

    dev_thread = threading.Thread(target=developer.run)
    test_thread = threading.Thread(target=tester.run)

    dev_thread.daemon = True
    test_thread.daemon = True

    dev_thread.start()
    test_thread.start()

    message_queue.put({
        "sender": "tester",
        "recipient": "developer",
        "type": "request",
        "content": "İlk kodu gönder"
    })

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Simülasyon durduruldu.")

if __name__ == "__main__":
    main()
