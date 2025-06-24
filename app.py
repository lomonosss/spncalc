import os
import uuid
import concurrent.futures
from flask import Flask, request, jsonify, send_file, render_template
from google import generativeai as genai
from pydub import AudioSegment
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Load API keys
GOOGLE_API_KEYS = os.getenv('GOOGLE_API_KEYS')
if GOOGLE_API_KEYS:
    API_KEYS = GOOGLE_API_KEYS.split(',')
else:
    API_KEYS = []

if not API_KEYS:
    print("WARNING: GOOGLE_API_KEYS environment variable not set or empty. TTS functionality will not work.")

# Configuration
TEXT_CHUNK_SIZE = 4800  # Max characters per chunk for Gemini API
TEMP_DIR = "temp_audio_chunks"
os.makedirs(TEMP_DIR, exist_ok=True)

def synthesize_chunk(text_chunk, api_key, voice_name, chunk_index):
    """Synthesizes a single text chunk using a given API key."""
    try:
        print(f"Synthesizing chunk {chunk_index} with key ending ...{api_key[-4:]}")
        genai.configure(api_key=api_key)

        # Model selection based on voice_name - this is a placeholder
        # Gemini's current Text-to-Speech might not have direct "male/female" voice names.
        # This needs to be adapted to the actual API's voice selection mechanism.
        # For now, we'll use a generic model or assume the API key is tied to a default voice.
        # The prompt below is a placeholder for what might be needed.
        # Actual implementation depends on the specific Gemini model and its TTS capabilities.

        # Placeholder: This part needs to be updated based on Gemini's TTS API specifics
        # For example, if the API uses specific voice model names:
        # model_name = "gemini-tts-voice-female" if voice_name == "female" else "gemini-tts-voice-male"
        # Or if it's part of the prompt / request structure.
        # As of my last update, direct TTS with voice selection in Gemini was through specific models
        # or parameters not just "male"/"female".
        # For this example, I'll assume a generic TTS model is available.
        # If a specific model is needed, it should be specified here.

        # This is a conceptual representation. The actual API call might differ.
        # It's highly likely that Gemini's TTS will be part of a multimodal model or a specific TTS endpoint.
        # The following is a generic placeholder for making a TTS request.
        # YOU WILL LIKELY NEED TO ADJUST THIS PART BASED ON THE ACTUAL GEMINI TTS API DOCUMENTATION.

        # Let's assume for now that the default model for the API key is used,
        # and voice differentiation might be less direct or require different models/prompts.
        # For the purpose of this structure, we'll proceed with a generic call.

        # This is a mock-up of what a call *might* look like.
        # response = genai.generate_text( # Or appropriate TTS function
        #     prompt=f"Synthesize the following text in a {voice_name} voice: {text_chunk}",
        #     # model="models/text-to-speech-model" # Placeholder for actual model
        # )
        # audio_content = response.audio_content # Assuming response has this attribute

        # --- SIMULATED API CALL FOR NOW ---
        # Since I cannot make actual API calls here and to show the structure,
        # I will simulate audio generation by creating a silent audio segment.
        # In a real scenario, this would be the actual API call and audio content retrieval.
        print(f"Simulating TTS for chunk {chunk_index}: '{text_chunk[:30]}...'")
        silence_duration = len(text_chunk) * 10 # ms, e.g. 10ms per char
        audio_segment = AudioSegment.silent(duration=silence_duration)
        # --- END OF SIMULATION ---

        # In a real scenario, you would get raw audio data (e.g., MP3, WAV bytes)
        # audio_segment = AudioSegment.from_file(io.BytesIO(audio_content), format="mp3") # Or other format

        temp_file_path = os.path.join(TEMP_DIR, f"chunk_{chunk_index}_{uuid.uuid4()}.mp3")
        audio_segment.export(temp_file_path, format="mp3")
        print(f"Chunk {chunk_index} saved to {temp_file_path}")
        return temp_file_path
    except Exception as e:
        print(f"Error synthesizing chunk {chunk_index} with key ...{api_key[-4:]}: {e}")
        # Propagate a more specific error or None to indicate failure
        raise RuntimeError(f"Failed to synthesize chunk {chunk_index}: {str(e)}")


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/synthesize', methods=['POST'])
def synthesize():
    if not API_KEYS:
        return jsonify({"error": "API keys are not configured on the server."}), 500

    data = request.get_json()
    text = data.get('text')
    voice = data.get('voice', 'female') # Default to female if not specified

    if not text:
        return jsonify({"error": "Text is required."}), 400

    text_chunks = [text[i:i + TEXT_CHUNK_SIZE] for i in range(0, len(text), TEXT_CHUNK_SIZE)]
    num_chunks = len(text_chunks)
    temp_audio_files = [None] * num_chunks # To store paths in correct order

    # Use a unique directory for this request's chunks to avoid filename collisions
    request_temp_dir = os.path.join(TEMP_DIR, str(uuid.uuid4()))
    os.makedirs(request_temp_dir, exist_ok=True)

    print(f"Processing {num_chunks} chunks for text of length {len(text)}.")

    # Using ProcessPoolExecutor for true parallelism
    # Note: If the genai library or its authentication is not process-safe,
    # ThreadPoolExecutor might be an alternative, but with GIL limitations for CPU-bound parts.
    # Assuming genai client can be configured per process.
    with concurrent.futures.ProcessPoolExecutor(max_workers=len(API_KEYS)) as executor:
        futures = {}
        for i, chunk in enumerate(text_chunks):
            api_key_for_chunk = API_KEYS[i % len(API_KEYS)]
            # Pass request_temp_dir to worker or ensure TEMP_DIR is used correctly
            # For simplicity, synthesize_chunk will use TEMP_DIR directly but ensure filenames are unique.
            # A better approach might be to pass a dedicated sub-folder per request.
            # Let's refine synthesize_chunk to accept a base temp_dir.
            # Modifying call to synthesize_chunk to include request_temp_dir for cleaner separation (conceptually)
            # However, synthesize_chunk currently uses global TEMP_DIR. Let's keep it simple for now with UUIDs.

            future = executor.submit(synthesize_chunk, chunk, api_key_for_chunk, voice, i)
            futures[future] = i # Store index to map back

        for future in concurrent.futures.as_completed(futures):
            original_index = futures[future]
            try:
                temp_file_path = future.result()
                if temp_file_path:
                    temp_audio_files[original_index] = temp_file_path
                else:
                    # Handle case where a chunk failed but didn't raise an exception that was caught by the main try-except
                    raise RuntimeError(f"Chunk {original_index} processing returned None.")
            except Exception as e:
                print(f"A chunk failed to process: {e}")
                # Cleanup already processed chunks for this request
                for f_path in temp_audio_files:
                    if f_path and os.path.exists(f_path):
                        try:
                            os.remove(f_path)
                        except OSError:
                            print(f"Error cleaning up temp file {f_path} during error handling.")
                if os.path.exists(request_temp_dir): # Clean the request specific temp dir
                     try:
                        # Make sure it's empty before removing, or use shutil.rmtree
                        for item in os.listdir(request_temp_dir):
                            item_path = os.path.join(request_temp_dir, item)
                            if os.path.isfile(item_path):
                                os.remove(item_path)
                        os.rmdir(request_temp_dir)
                     except Exception as cleanup_error:
                        print(f"Error cleaning up request temp directory {request_temp_dir}: {cleanup_error}")
                return jsonify({"error": f"Failed to generate audio for all chunks. {str(e)}"}), 500

    if None in temp_audio_files:
        # This case should ideally be caught by the exception handling above.
        # Cleanup any files that were created
        for f_path in temp_audio_files:
            if f_path and os.path.exists(f_path):
                os.remove(f_path)
        # Consider removing request_temp_dir here as well
        return jsonify({"error": "One or more audio chunks could not be generated."}), 500

    print(f"All chunks processed: {temp_audio_files}")

    # Concatenate audio files
    try:
        final_audio = AudioSegment.empty()
        for temp_file_path in temp_audio_files:
            if not temp_file_path or not os.path.exists(temp_file_path): # Should not happen if checks above are fine
                raise ValueError(f"Missing or invalid temp file path: {temp_file_path}")
            chunk_audio = AudioSegment.from_mp3(temp_file_path)
            final_audio += chunk_audio

        final_output_filename = f"final_audio_{uuid.uuid4()}.mp3"
        final_output_path = os.path.join(TEMP_DIR, final_output_filename) # Store final audio also in TEMP_DIR temporarily
        final_audio.export(final_output_path, format="mp3")
        print(f"Final audio exported to {final_output_path}")

    except Exception as e:
        print(f"Error concatenating audio files: {e}")
        return jsonify({"error": f"Failed to concatenate audio files: {str(e)}"}), 500
    finally:
        # Cleanup individual chunk files
        for temp_file_path in temp_audio_files:
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                    print(f"Cleaned up temp chunk file: {temp_file_path}")
                except OSError as e:
                    print(f"Error deleting temp chunk file {temp_file_path}: {e}")
        # Cleanup the request-specific temporary directory if it's empty
        # This logic might need to be more robust if other files could be in request_temp_dir
        try:
            if os.path.exists(request_temp_dir) and not os.listdir(request_temp_dir):
                os.rmdir(request_temp_dir)
                print(f"Cleaned up request temp directory: {request_temp_dir}")
        except OSError as e:
            print(f"Error deleting request temp directory {request_temp_dir}: {e}")


    # Send the file and then clean it up
    try:
        return send_file(
            final_output_path,
            as_attachment=True,
            download_name='synthesized_audio.mp3',
            mimetype='audio/mpeg'
        )
    finally:
        # Clean up the final concatenated file after sending
        if os.path.exists(final_output_path):
            try:
                os.remove(final_output_path)
                print(f"Cleaned up final audio file: {final_output_path}")
            except OSError as e:
                print(f"Error deleting final audio file {final_output_path}: {e}")

if __name__ == '__main__':
    # Make sure to set GOOGLE_API_KEYS in your environment
    # For development, you can use:
    # GOOGLE_API_KEYS="key1,key2" python app.py
    if not API_KEYS:
        print("FATAL: No API keys loaded. Please set the GOOGLE_API_KEYS environment variable.")
        print("Example: GOOGLE_API_KEYS=\"fakekey1,fakekey2,fakekey3\"")
    else:
        print(f"Loaded {len(API_KEYS)} API keys.")

    app.run(debug=True, host='0.0.0.0', port=5000)
