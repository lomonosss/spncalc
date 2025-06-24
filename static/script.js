document.addEventListener('DOMContentLoaded', () => {
    const textInput = document.getElementById('text-input');
    const voiceSelect = document.getElementById('voice-select');
    const generateBtn = document.getElementById('generate-btn');
    const btnText = generateBtn.querySelector('.btn-text');
    const loader = generateBtn.querySelector('.loader');
    const statusArea = document.getElementById('status-area');
    const downloadArea = document.getElementById('download-area');

    const originalButtonText = btnText.textContent;

    generateBtn.addEventListener('click', async () => {
        const text = textInput.value.trim();
        const voice = voiceSelect.value;

        if (!text) {
            updateStatus('Please enter some text to synthesize.', true);
            return;
        }

        // Disable button and show loader
        generateBtn.disabled = true;
        btnText.textContent = 'Processing...';
        btnText.classList.add('processing');
        loader.style.display = 'inline-block';

        updateStatus('Initializing synthesis...');
        downloadArea.innerHTML = ''; // Clear previous download link

        try {
            updateStatus('Sending request to the server...');
            const response = await fetch('/synthesize', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text, voice }),
            });

            if (!response.ok) {
                let errorMsg = `Server error: ${response.status}`;
                try {
                    const errorData = await response.json();
                    // errorData could be {error: "message"} or {error: "message", details: "..."}
                    // or {message: "...", chunk_index: X} from our custom backend error
                    if (errorData.error) {
                        errorMsg = errorData.error;
                        if (errorData.details) {
                             errorMsg += ` Details: ${errorData.details}`;
                        }
                    } else if (errorData.message) {
                        errorMsg = errorData.message;
                        if (typeof errorData.chunk_index !== 'undefined') {
                            errorMsg = `Error in chunk ${errorData.chunk_index}: ${errorData.message}`;
                        }
                    }
                } catch (e) {
                    // If response is not JSON or another error occurs
                    const textError = await response.text();
                    errorMsg = textError || errorMsg; // Use text error if available
                    console.warn("Failed to parse error response as JSON:", e);
                }
                throw new Error(errorMsg);
            }

            updateStatus('Audio received from server! Preparing download...');
            const blob = await response.blob();

            if (blob.type !== 'audio/mpeg') {
                // This might happen if the server sent a JSON error response with a 200 OK for some reason,
                // or if the response is not an MP3.
                let errorText = "Received unexpected data type from server. Expected audio/mpeg.";
                try {
                    // Try to read as text to see if it's an error message
                    const text = await blob.text();
                    errorText += ` Server response: ${text.substring(0,1000)}`; // Log part of it
                } catch(e){}
                throw new Error(errorText);
            }

            const url = URL.createObjectURL(blob);

            const downloadLink = document.createElement('a');
            downloadLink.href = url;
            downloadLink.download = 'synthesized_audio.mp3';
            downloadLink.textContent = 'Download Generated Audio';

            downloadArea.appendChild(downloadLink);
            updateStatus('Success! Your audio is ready for download.', false);

        } catch (error) {
            console.error('Synthesis process error:', error);
            updateStatus(`Error: ${error.message}`, true);
        } finally {
            // Re-enable button and restore original text/hide loader
            generateBtn.disabled = false;
            btnText.textContent = originalButtonText;
            btnText.classList.remove('processing');
            loader.style.display = 'none';
        }
    });

    function updateStatus(message, isError = false) {
        statusArea.textContent = message;
        if (isError) {
            statusArea.classList.add('error');
        } else {
            statusArea.classList.remove('error');
        }
    }
});
