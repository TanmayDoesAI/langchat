// scripts.js
var docModalInstance = new bootstrap.Modal(document.getElementById('docModal'), {});
document.addEventListener('DOMContentLoaded', () => {
    const sendButton = document.getElementById('send-button');
    const queryInput = document.getElementById('query-input');
    const chatBody = document.getElementById('chat-body');
    const sourceDocuments = document.getElementById('source-documents');
    const docModal = new bootstrap.Modal(document.getElementById('docModal'), {});
    const modalBody = document.getElementById('modal-body');

    // Function to append message to chat window
    function appendMessage(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', role);

        const messageContent = document.createElement('div');
        messageContent.classList.add('message-content');

        if (role === 'assistant') {
            // Parse markdown content for assistant's messages
            messageContent.innerHTML = marked.parse(content);
        } else {
            // Escape HTML for user's messages to prevent XSS
            messageContent.textContent = content;
        }

        const timestamp = document.createElement('div');
        timestamp.classList.add('timestamp');
        const now = new Date();
        timestamp.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        messageContent.appendChild(timestamp);
        messageDiv.appendChild(messageContent);
        chatBody.appendChild(messageDiv);

        // Highlight code blocks
        messageContent.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });
        chatBody.scrollTop = chatBody.scrollHeight;
    }
    function linkify(text) {
        const urlRegex = /https?:\/\/[^\s"']+/g;
        return text.replace(urlRegex, (url) => {
            return `<a href="${url}" target="_blank">${url}</a>`;
        });
    }
    // Function to handle sending message
    function sendMessage() {
        const message = queryInput.value.trim();
        if (message === '') return;

        // Append user message
        appendMessage('user', message);
        queryInput.value = '';

        // Disable input and button
        queryInput.disabled = true;
        sendButton.disabled = true;

        // Send POST request to API
        fetch('http://127.0.0.1:8000/api/chat', { // Replace with your backend URL
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question: message })
        })
        .then(response => response.json())
        .then(data => {
            if (data.detail) {
                appendMessage('assistant', `Error: ${data.detail}`);
            } else {
                const answer = data.answer;
                appendMessage('assistant', answer);

                // Display source documents
                const sources = data.sources;
                displaySources(sources);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            appendMessage('assistant', 'Sorry, something went wrong.');
        })
        .finally(() => {
            // Re-enable input and button
            queryInput.disabled = false;
            sendButton.disabled = false;
            queryInput.focus();
        });
    }

    // // Function to display source documents
    // function displaySources(sources) {
    //     sourceDocuments.innerHTML = ''; // Clear previous sources
    //     sources.forEach((doc, index) => {
    //         const listItem = document.createElement('li');
    //         listItem.classList.add('list-group-item', 'source-item');
    //         listItem.innerHTML = `<strong>Source ${index + 1}:</strong> ${doc.source}`;
    //         listItem.addEventListener('click', () => {
    //             modalBody.textContent = `Source: ${doc.source}\n\n${doc.text}`;
    //             docModal.show();
    //         });
    //         sourceDocuments.appendChild(listItem);
    //     });
    // }
    function displaySources(sources) {
        sourceDocuments.innerHTML = ''; // Clear previous sources
        sources.forEach((doc, index) => {
            const listItem = document.createElement('li');
            listItem.classList.add('list-group-item', 'source-item');
            const linkedSource = linkify(doc.source);
            listItem.innerHTML = `<strong>Source ${index + 1}:</strong> ${linkedSource}`;
            listItem.addEventListener('click', () => {
                // Linkify source and text
                const linkedDocSource = linkify(doc.source);
                const linkedDocText = linkify(doc.text);
                // Set modal content
                const modalBody = document.getElementById('modal-body');
                modalBody.innerHTML = `
                    <p><strong>Source:</strong> ${linkedDocSource}</p>
                    <p><strong>Text:</strong> ${linkedDocText}</p>
                `;
                // Show the modal
                docModalInstance.show();
            });
            sourceDocuments.appendChild(listItem);
        });
    }
    // Event listeners
    sendButton.addEventListener('click', sendMessage);
    queryInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
});
