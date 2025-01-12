from flask import Flask, render_template, request, jsonify
from rag_chatbot import VisionChatbot
import os
from dotenv import load_dotenv
import tempfile

load_dotenv()

app = Flask(__name__)

# Initialize chatbot without passing api_token as a named parameter
hf_token = os.getenv("HUGGING_FACE_TOKEN")
if not hf_token:
    raise ValueError("HUGGING_FACE_TOKEN not found in environment variables")
chatbot = VisionChatbot()  # The class will get the token from environment variables

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    tmp_path = None
    try:
        data = request.form
        query = data.get('query')
        uploaded_file = request.files.get('file')
        
        if uploaded_file:
            file_ext = uploaded_file.filename.split('.')[-1].lower()
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as tmp_file:
                tmp_path = tmp_file.name
                uploaded_file.save(tmp_path)
            
            try:
                response = chatbot.generate_response(
                    file_path=tmp_path,
                    text_prompt=query,
                    file_type=file_ext
                )
            finally:
                # Ensure file cleanup in a finally block
                if tmp_path and os.path.exists(tmp_path):
                    try:
                        os.unlink(tmp_path)
                    except Exception as e:
                        print(f"Error cleaning up temporary file: {e}")
        else:
            response = chatbot.generate_response(text_prompt=query)
            
        return jsonify({"response": response}), 200
    
    except Exception as e:
        # Ensure cleanup even if an error occurs
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception as cleanup_error:
                print(f"Error cleaning up temporary file: {cleanup_error}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 