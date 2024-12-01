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

    // Function to parse sources from the sources string
    function parseSources(sourcesString) {
        const sources = [];
        const lines = sourcesString.split('\n');
        let currentSource = null;

        lines.forEach(line => {
            if (line.startsWith('- **Source:**')) {
                // If we have a currentSource, push it
                if (currentSource) {
                    sources.push(currentSource);
                }
                const sourceUrlMatch = line.match(/- \*\*Source:\*\* (.*)/);
                if (sourceUrlMatch) {
                    const sourceUrl = sourceUrlMatch[1].trim();
                    currentSource = { source: sourceUrl, text: '' };
                }
            } else if (line.startsWith('  **Text:**')) {
                const textMatch = line.match(/  \*\*Text:\*\* (.*)/);
                if (textMatch && currentSource) {
                    currentSource.text = textMatch[1].trim();
                }
            } else if (currentSource && line.trim() !== '') {
                currentSource.text += '\n' + line.trim();
            }
        });
        // Add the last source
        if (currentSource) {
            sources.push(currentSource);
        }
        return sources;
    }

    // Function to handle sending message
    function sendMessage() {
        const message = queryInput.value.trim();
        if (message === '') return;

        console.log('User Message:', message); // Log user's input

        // Append user message
        appendMessage('user', message);
        queryInput.value = '';

        // Disable input and button
        queryInput.disabled = true;
        sendButton.disabled = true;

        // Initialize conversation history if not present
        if (!window.conversationHistory) {
            window.conversationHistory = [];
        }

        // Add the user's message to the conversation history
        window.conversationHistory.push([message, null]);
        console.log('Conversation History:', window.conversationHistory); // Log conversation history

        // Prepare data for POST request
        const data = {
            data: [
                message,
                window.conversationHistory,
                "# Hello!"
            ]
        };

        console.log('Data to be sent:', data); // Log the data being sent to the API

        // Send POST request to API
        fetch('https://tanmay09516-langchat-backend.hf.space/gradio_api/call/respond', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => {
            console.log('POST Response:', response); // Log the raw response
            return response.json();
        })
        .then(postResponse => {
            console.log('Parsed POST Response:', postResponse); // Log the parsed response

            // Extract the event ID from the response
            const eventId = postResponse['event_id'];
            if (!eventId) {
                console.error('Event ID not found in response:', postResponse); // Log the error and response
                throw new Error('Event ID not found in response');
            }

            console.log('Event ID:', eventId); // Log the Event ID

            // Now make a GET request to get the assistant's response
            return fetch('https://tanmay09516-langchat-backend.hf.space/gradio_api/call/respond/' + eventId);
        })
        .then(response => {
            return response.text(); // Get the response as text
        })
        .then(getResponse => {
            console.log('Parsed GET Response:', getResponse); // Log the parsed GET response

            // Parse the SSE-formatted response
            const events = getResponse.split('\n\n');
            let assistantReply = null;
            let sources = [];

            events.forEach(event => {
                const lines = event.split('\n');
                let eventName = '';
                let data = '';

                lines.forEach(line => {
                    if (line.startsWith('event: ')) {
                        eventName = line.slice('event: '.length);
                    } else if (line.startsWith('data: ')) {
                        data += line.slice('data: '.length);
                    }
                });

                if (eventName === 'complete') {
                    console.log('Data from complete event:', data);
                    try {
                        const parsedData = JSON.parse(data);
                        console.log('Parsed data:', parsedData);

                        // Extract assistant's reply from the parsed data
                        const conversationHistory = parsedData[0];
                        const lastTurn = conversationHistory[conversationHistory.length - 1];
                        assistantReply = lastTurn[1]; // Assistant's message

                        console.log('Assistant Response:', assistantReply);

                        // Extract sources from parsedData[2] if it exists
                        const sourcesString = parsedData[2];
                        console.log('Sources String:', sourcesString);

                        if (sourcesString) {
                            // Parse sourcesString to extract sources
                            sources = parseSources(sourcesString);
                            console.log('Extracted Sources:', sources);
                        } else {
                            console.log('No sources found.');
                        }
                    } catch (e) {
                        console.error('Error parsing JSON:', e);
                    }
                }
            });

            if (assistantReply === null) {
                throw new Error('Assistant response not found in the GET response.');
            }

            // Append assistant's message
            appendMessage('assistant', assistantReply);

            // Add the assistant's response to the conversation history
            window.conversationHistory.push([null, assistantReply]);

            // Display the sources if any
            if (sources.length > 0) {
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
