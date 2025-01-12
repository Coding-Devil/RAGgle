from flask import Flask, render_template, request, jsonify
from utils.rag_chatbot import VisionChatbot
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, 
    static_folder='../static',
    template_folder='../templates'
)

# Initialize chatbot
hf_token = os.getenv("HUGGING_FACE_TOKEN")
chatbot = VisionChatbot()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    # Your existing chat endpoint code
    pass

if __name__ == '__main__':
    app.run() 