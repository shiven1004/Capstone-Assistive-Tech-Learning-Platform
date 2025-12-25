# main.py
from question_generator import generate_test
from logger import Logger
import re

LOG = Logger("Main Logger", log_file_needed=True, log_file_path="Logs/main.log", level='DEV')

if __name__ == "__main__":
    try:
        print("🚀 Starting test generation...")
        result = generate_test()
        
        with open("generated_test.txt", "w", encoding="utf-8") as f:
            f.write(result)

        qcount = len(re.findall(r"^\d+\.\s", result, re.MULTILINE))
        
        print("\n" + "="*50)
        print("✅ Test generation completed!")
        print(f"📊 Questions generated: {qcount}/80")
        print(f"📁 File saved: generated_test.txt")
        
        if qcount == 100:
            print("🎯 SUCCESS: All 80 questions generated!")
        else:
            print(f"⚠️  WARNING: Expected 80 questions, got {qcount}")
            print("💡 Check logs for parsing issues")
        
        print("🌐 Universal content, guided by examples")
        print("="*50)

    except Exception as e:
        LOG.error(f"Generation failed: {e}")
        print(f"❌ Generation failed: {e}")
        raise
