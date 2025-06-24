document.addEventListener('DOMContentLoaded', () => {
    const textInput = document.getElementById('text-input');
    const voiceSelect = document.getElementById('voice-select');
    const generateBtn = document.getElementById('generate-btn');
    const statusArea = document.getElementById('status-area');
    const downloadArea = document.getElementById('download-area');

    let originalButtonText = generateBtn.innerHTML;

    generateBtn.addEventListener('click', async () => {
        const text = textInput.value.trim();
        const voice = voiceSelect.value;

        if (!text) {
            statusArea.textContent = 'Please enter some text.';
            return;
        }

        // Disable button and show loader
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<span class="loader"></span>Processing...';
        statusArea.textContent = 'Initializing synthesis...';
        downloadArea.innerHTML = ''; // Clear previous download link

        try {
            statusArea.textContent = 'Sending request to server...';
            const response = await fetch('/synthesize', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text, voice }),
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: 'Failed to process error response from server.' }));
                throw new Error(errorData.error || `Server error: ${response.status}`);
            }

            statusArea.textContent = 'Audio received! Preparing download...';
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);

            const downloadLink = document.createElement('a');
            downloadLink.href = url;
            downloadLink.download = 'synthesized_audio.mp3';
            downloadLink.textContent = 'Download Audio';

            downloadArea.appendChild(downloadLink);
            statusArea.textContent = 'Done! Your download is ready.';

        } catch (error) {
            console.error('Synthesis error:', error);
            statusArea.textContent = `Error: ${error.message}`;
        } finally {
            // Re-enable button and restore original text
            generateBtn.disabled = false;
            generateBtn.innerHTML = originalButtonText;
        }
    });
});
