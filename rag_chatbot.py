try:
    import torch
except ImportError:
    print("PyTorch import failed, attempting to continue without it...")

from huggingface_hub import InferenceClient
import torch
from PIL import Image
import base64
from io import BytesIO
import os
from dotenv import load_dotenv
import fitz  # PyMuPDF for PDF processing
import textwrap
import functools
import time

# Load environment variables
load_dotenv()

class VisionChatbot:
    def __init__(self):
        self.model_name = "meta-llama/Llama-3.2-11B-Vision-Instruct"
        self.api_token = os.getenv("HUGGING_FACE_TOKEN")
        if not self.api_token:
            raise ValueError("HUGGING_FACE_TOKEN not found in environment variables")
        
        # Initialize inference client with correct parameter name 'token'
        self.client = InferenceClient(token=self.api_token)
        
        # Maximum context length for the model
        self.max_chunk_size = 2000
        
        # Add a simple cache for responses
        self._cache = {}
        self._cache_timeout = 3600  # 1 hour cache timeout
    
    @functools.lru_cache(maxsize=100)
    def _get_cached_response(self, query_key):
        """Cache responses to avoid repeated API calls"""
        return self._cache.get(query_key)
    
    def _cache_response(self, query_key, response):
        """Store response in cache with timestamp"""
        self._cache[query_key] = {
            'response': response,
            'timestamp': time.time()
        }
    
    def process_image(self, image_path):
        """Convert image to base64 URL format"""
        with Image.open(image_path) as img:
            if img.mode != "RGB":
                img = img.convert("RGB")
            
            buffered = BytesIO()
            img.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            return f"data:image/jpeg;base64,{img_str}"

    def extract_text_from_pdf(self, pdf_path):
        """Extract text from PDF file"""
        text = ""
        try:
            with fitz.open(pdf_path) as doc:
                # Process each page
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    # Extract text with formatting information
                    text += f"\n=== Page {page_num + 1} ===\n"
                    text += page.get_text("text")  # Use "text" format for better structure
                    text += "\n"
            return text.strip()
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")

    def chunk_text(self, text, max_chars=2000):
        """Split text into chunks of maximum size"""
        return textwrap.wrap(text, max_chars, break_long_words=False, break_on_hyphens=False)

    def generate_response(self, file_path=None, text_prompt="", file_type=None):
        """Generate response using the Inference API with caching"""
        # Create a unique key for caching
        cache_key = f"{file_path}:{text_prompt}"
        
        # Check cache first
        cached = self._get_cached_response(cache_key)
        if cached and (time.time() - cached['timestamp'] < self._cache_timeout):
            return cached['response']
        
        try:
            if file_path:
                if file_type == "pdf":
                    # Handle PDF
                    text = self.extract_text_from_pdf(file_path)
                    chunks = self.chunk_text(text)
                    
                    # Create a more detailed prompt
                    summary_prompt = (
                        f"Here is the content from a PDF document:\n\n"
                        f"{chunks[0]}\n\n"  # First chunk
                    )
                    
                    # Add more chunks if they exist
                    if len(chunks) > 1:
                        summary_prompt += (
                            f"Additional content:\n{chunks[1]}\n\n"  # Second chunk
                            f"[Document continues for {len(chunks)} total sections...]\n\n"
                        )
                    
                    # Add the user's question
                    summary_prompt += (
                        f"Based on this document content, please answer the following question:\n"
                        f"{text_prompt if text_prompt else 'Please provide a detailed summary of this document.'}"
                    )
                    
                    messages = [{
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": summary_prompt
                            }
                        ]
                    }]
                    
                    # Use a system message to guide the response
                    messages.insert(0, {
                        "role": "system",
                        "content": [
                            {
                                "type": "text",
                                "text": "You are a helpful assistant that provides accurate information based on the given document content. If the information isn't in the document, say so clearly."
                            }
                        ]
                    })
                
                elif file_type in ["jpg", "jpeg", "png"]:
                    # Handle image
                    messages = [{
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": text_prompt if text_prompt else "Describe this image."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": self.process_image(file_path)
                                }
                            }
                        ]
                    }]
            else:
                # Enhanced text-only query handling
                messages = [
                    {
                        "role": "system",
                        "content": [
                            {
                                "type": "text",
                                "text": "You are a helpful and friendly AI assistant. Provide clear, informative, and engaging responses while maintaining a natural conversational tone."
                            }
                        ]
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": text_prompt
                            }
                        ]
                    }
                ]

            # Stream the response with increased max_tokens
            stream = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=1000,
                temperature=0.7,
                stream=True
            )

            # Collect the streamed response
            response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    response += chunk.choices[0].delta.content

            # Cache the response before returning
            self._cache_response(cache_key, response)
            return response
            
        except Exception as e:
            raise Exception(f"Error generating response: {str(e)}") 
