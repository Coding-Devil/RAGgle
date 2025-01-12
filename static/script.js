document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chatForm');
    const queryInput = document.getElementById('queryInput');
    const chatContainer = document.getElementById('chatContainer');
    const fileUpload = document.getElementById('fileUpload');
    const filePreview = document.getElementById('filePreview');
    const fileName = document.getElementById('fileName');
    const removeFile = document.getElementById('removeFile');
    const imagePreview = document.getElementById('imagePreview');

    let currentFile = null;

    // Auto-resize textarea
    queryInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });

    // Handle Enter key
    queryInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event('submit'));
        }
    });

    // File upload handling
    fileUpload.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            currentFile = file;
            fileName.textContent = file.name;
            filePreview.classList.remove('hidden');
            
            // Clear previous preview
            imagePreview.innerHTML = '';
            
            // Preview image if it's an image file
            if (file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    const img = document.createElement('img');
                    img.src = e.target.result;
                    img.classList.add('rounded-lg');
                    imagePreview.appendChild(img);
                };
                reader.readAsDataURL(file);
            }
        }
    });

    removeFile.addEventListener('click', () => {
        currentFile = null;
        fileUpload.value = '';
        filePreview.classList.add('hidden');
        fileName.textContent = '';
        imagePreview.innerHTML = '';
    });

    function addMessage(type, content) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', `${type}-message`);
        
        const contentDiv = document.createElement('div');
        contentDiv.classList.add('message-content');

        let icon, formattedContent;
        
        switch(type) {
            case 'user':
                icon = '👤';
                formattedContent = `<div class="text-white text-lg font-medium">${content}</div>`;
                break;
            case 'assistant':
                icon = '🤖';
                formattedContent = marked.parse(content);
                break;
            case 'error':
                icon = '❌';
                formattedContent = `<div class="text-red-400 text-lg">${content}</div>`;
                break;
        }

        contentDiv.innerHTML = `
            <div class="flex items-start ${type === 'user' ? 'justify-end' : 'justify-start'} gap-6">
                ${type !== 'user' ? `
                    <div class="flex-shrink-0 mt-1">
                        <div class="avatar w-11 h-11 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 
                                    flex items-center justify-center shadow-lg text-xl">
                            ${icon}
                        </div>
                    </div>
                ` : ''}
                <div class="flex-grow prose prose-lg max-w-none">
                    ${formattedContent}
                </div>
                ${type === 'user' ? `
                    <div class="flex-shrink-0 mt-1">
                        <div class="avatar w-11 h-11 rounded-full bg-gradient-to-r from-purple-600 to-blue-500 
                                    flex items-center justify-center shadow-lg text-xl">
                            ${icon}
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
        
        messageDiv.appendChild(contentDiv);
        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const query = queryInput.value.trim();
        
        if (!query) return;

        // Add user message
        addMessage('user', query);
        queryInput.value = '';
        queryInput.style.height = 'auto';

        // Prepare form data
        const formData = new FormData();
        formData.append('query', query);
        if (currentFile) {
            formData.append('file', currentFile);
        }

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                body: formData,
                headers: {
                    'Accept': 'application/json'
                }
            });

            const data = await response.json();
            
            if (response.ok) {
                addMessage('assistant', data.response);
            } else {
                addMessage('error', data.error || 'An error occurred');
            }
        } catch (error) {
            addMessage('error', 'Failed to send message');
        }
    });
}); 