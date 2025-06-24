import os
import uuid
import concurrent.futures
import traceback # For detailed error logging
import io # For handling byte streams if needed for genai
from flask import Flask, request, jsonify, send_file, render_template
from google.generativeai importGenerativeModel # Placeholder for actual Gemini TTS client/model
from pydub import AudioSegment
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# --- Configuration ---
GOOGLE_API_KEYS = os.getenv('GOOGLE_API_KEYS')
API_KEYS = [key.strip() for key in GOOGLE_API_KEYS.split(',')] if GOOGLE_API_KEYS else []

if not API_KEYS:
    print("WARNING: GOOGLE_API_KEYS environment variable not set or empty. TTS functionality will be simulated and may not work as expected with actual API calls.")

TEXT_CHUNK_SIZE = 4800  # Max characters per chunk (Gemini Pro limit is often higher, but TTS specific models might differ)
SILENCE_BETWEEN_CHUNKS_MS = 500 # 500ms silence
TEMP_AUDIO_DIR = "temp_audio_chunks"
os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)

# --- TTS Worker Function ---
def synthesize_chunk_worker(text_chunk, api_key_for_chunk, voice_name_placeholder, chunk_index, request_temp_dir):
    """
    Synthesizes a single text chunk using a given API key.
    This function is designed to be run in a separate process.
    voice_name_placeholder: Actual Gemini API might use model names or other params for voice.
    """
    # In a real scenario, genai.configure(api_key=api_key_for_chunk) might be needed here
    # if the client isn't configured globally or per-instance in the main thread.
    # For ProcessPoolExecutor, each process should configure its own client instance.

    # genai.configure(api_key=api_key_for_chunk) # Potentially needed per process
    # model = GenerativeModel('gemini-pro') # Or specific TTS model

    temp_file_path = os.path.join(request_temp_dir, f"chunk_{chunk_index}_{uuid.uuid4()}.mp3")

    try:
        print(f"[Chunk {chunk_index}] Starting synthesis with key ending ...{api_key_for_chunk[-4:] if api_key_for_chunk else 'N/A'}.")

        # --- !!! ACTUAL GEMINI API CALL SIMULATION !!! ---
        # Replace this block with actual google.generativeai calls for Text-to-Speech
        # The exact API (e.g., genai.text_to_speech(), or a method on a model instance)
        # and parameters (for voice, output format etc.) will depend on the Gemini SDK version
        # and the specific TTS model you intend to use.

        if not api_key_for_chunk or "YOUR_GOOGLE_API_KEY" in api_key_for_chunk: # Basic check for placeholder key
            print(f"[Chunk {chunk_index}] SIMULATING TTS due to placeholder or missing API key.")
            # Simulate varying lengths for silence based on text length
            silence_duration_ms = len(text_chunk) * 5 # Rough estimate: 5ms per character for simulation
            audio_content_simulated = AudioSegment.silent(duration=silence_duration_ms)
        else:
            # This is where you'd put the real call:
            # print(f"[Chunk {chunk_index}] Attempting REAL API call (conceptual)...")
            # response = model.generate_content( # This is a generic Gemini call, TTS will be specific
            #     f"Speak this in a {voice_name_placeholder} voice: {text_chunk}"
            #     # ... other parameters like voice selection, audio config ...
            # )
            # audio_bytes = response.candidates[0].content.parts[0].inline_data.data # Highly speculative path to audio bytes
            # audio_content_simulated = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3") # Or appropriate format
            # For now, still simulating as no live API calls allowed here.
            print(f"[Chunk {chunk_index}] SIMULATING TTS as live API calls are not enabled in this environment.")
            silence_duration_ms = len(text_chunk) * 5
            audio_content_simulated = AudioSegment.silent(duration=silence_duration_ms)

        # --- END OF SIMULATION ---

        audio_content_simulated.export(temp_file_path, format="mp3")
        print(f"[Chunk {chunk_index}] Successfully synthesized and saved to {temp_file_path}")
        return {"status": "success", "path": temp_file_path, "chunk_index": chunk_index}

    except Exception as e:
        print(f"!!!!!! ERROR in synthesize_chunk_worker for chunk {chunk_index} !!!!!!")
        print(f"Text (first 50 chars): {text_chunk[:50]}")
        print(f"API Key Used (last 4): ...{api_key_for_chunk[-4:] if api_key_for_chunk else 'N/A'}")
        print(f"Voice Placeholder: {voice_name_placeholder}")
        print("--- Full Traceback ---")
        traceback.print_exc() # Logs full traceback to console (where Flask server runs)
        print("--- End Traceback ---")

        error_message = f"Error during synthesis of chunk {chunk_index}: {type(e).__name__} - {str(e)}"
        # Attempt to remove partially created file if it exists
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except OSError:
                print(f"[Chunk {chunk_index}] Error: Could not remove partially created temp file {temp_file_path} during error handling.")
        return {"status": "error", "message": error_message, "chunk_index": chunk_index, "error_type": type(e).__name__}


# --- Flask Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/synthesize', methods=['POST'])
def synthesize_route():
    if not API_KEYS:
        return jsonify({"error": "API keys are not configured on the server. Please set GOOGLE_API_KEYS."}), 500

    data = request.get_json()
    text = data.get('text')
    voice_selection = data.get('voice', 'female') # Placeholder, actual use depends on Gemini API

    if not text:
        return jsonify({"error": "Text input is required."}), 400

    text_chunks = [text[i:i + TEXT_CHUNK_SIZE] for i in range(0, len(text), TEXT_CHUNK_SIZE)]
    num_chunks = len(text_chunks)

    # Create a unique temporary directory for this request's audio chunks
    request_specific_temp_dir = os.path.join(TEMP_AUDIO_DIR, str(uuid.uuid4()))
    os.makedirs(request_specific_temp_dir, exist_ok=True)

    print(f"Processing {num_chunks} chunks in directory: {request_specific_temp_dir}")

    chunk_results = [None] * num_chunks
    successful_audio_files_ordered = []

    with concurrent.futures.ProcessPoolExecutor(max_workers=len(API_KEYS)) as executor:
        future_to_chunk_index = {}
        for i, chunk_text in enumerate(text_chunks):
            api_key = API_KEYS[i % len(API_KEYS)]
            future = executor.submit(synthesize_chunk_worker, chunk_text, api_key, voice_selection, i, request_specific_temp_dir)
            future_to_chunk_index[future] = i

        for future in concurrent.futures.as_completed(future_to_chunk_index):
            original_index = future_to_chunk_index[future]
            try:
                result = future.result()
                chunk_results[original_index] = result
            except Exception as e: # Should ideally be caught within the worker
                print(f"Critical error from ProcessPoolExecutor future for chunk {original_index}: {e}")
                traceback.print_exc()
                chunk_results[original_index] = {"status": "error", "message": f"Future संकल्पना में त्रुटि: {str(e)}", "chunk_index": original_index, "error_type": type(e).__name__}


    # Check results and prepare for concatenation
    any_errors = False
    first_error_details = None
    for i, result in enumerate(chunk_results):
        if not result or result.get("status") == "error":
            any_errors = True
            print(f"Error in chunk {i}: {result.get('message', 'Unknown error') if result else 'No result'}")
            if not first_error_details: # Capture the first error for frontend
                 first_error_details = result if result else {"message": f"Chunk {i} failed processing with no details.", "chunk_index": i}
            # No need to add to successful_audio_files_ordered if it failed
        else:
            successful_audio_files_ordered.append(result.get("path")) # Add path of successful chunk

    if any_errors:
        # Cleanup all files in request_specific_temp_dir on any error
        for item in os.listdir(request_specific_temp_dir):
            item_path = os.path.join(request_specific_temp_dir, item)
            try:
                if os.path.isfile(item_path): os.remove(item_path)
            except Exception as e_clean:
                print(f"Error cleaning up {item_path} during error handling: {e_clean}")
        try:
            os.rmdir(request_specific_temp_dir)
        except Exception as e_rmdir:
            print(f"Error removing temp directory {request_specific_temp_dir}: {e_rmdir}")

        # Return the first encountered error to the frontend
        error_to_send = {
            "error": "Failed to generate audio for one or more chunks.",
            "details": first_error_details.get("message", "No specific error message available."),
            "chunk_index": first_error_details.get("chunk_index", -1),
            "error_type": first_error_details.get("error_type", "UnknownError")
        }
        return jsonify(error_to_send), 500

    if not successful_audio_files_ordered: # Should be caught by any_errors if chunk_results was populated
        return jsonify({"error": "No audio chunks were successfully generated."}), 500

    # Concatenate audio files with silence
    final_audio = AudioSegment.empty()
    silence_segment = AudioSegment.silent(duration=SILENCE_BETWEEN_CHUNKS_MS)

    try:
        for i, file_path in enumerate(successful_audio_files_ordered):
            if not file_path or not os.path.exists(file_path):
                # This should not happen if logic above is correct
                raise ValueError(f"Missing or invalid temp file path: {file_path} for chunk index {i}") # Find original index if needed

            chunk_audio = AudioSegment.from_mp3(file_path)
            final_audio += chunk_audio
            if i < len(successful_audio_files_ordered) - 1: # Don't add silence after the last chunk
                final_audio += silence_segment

        final_output_filename = f"final_audio_{uuid.uuid4()}.mp3"
        # Store final audio in main TEMP_AUDIO_DIR, not request_specific_temp_dir as that will be deleted
        final_output_path = os.path.join(TEMP_AUDIO_DIR, final_output_filename)
        final_audio.export(final_output_path, format="mp3")
        print(f"Final audio successfully concatenated to {final_output_path} with {SILENCE_BETWEEN_CHUNKS_MS}ms silence between chunks.")

    except Exception as e:
        print(f"Error during audio concatenation: {e}")
        traceback.print_exc()
        # Cleanup successful_audio_files_ordered and request_specific_temp_dir as concatenation failed
        return jsonify({"error": f"Failed to concatenate audio files: {str(e)}"}), 500
    finally:
        # Cleanup individual chunk files and the request-specific directory
        for file_path in successful_audio_files_ordered: # These are paths of successfully processed chunks
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError as e_clean:
                    print(f"Error deleting temp chunk file {file_path}: {e_clean}")
        try:
            if os.path.exists(request_specific_temp_dir) and not os.listdir(request_specific_temp_dir): # Check if empty
                os.rmdir(request_specific_temp_dir)
            elif os.path.exists(request_specific_temp_dir): # If not empty, something went wrong or there are other files
                 print(f"Warning: Request temp directory {request_specific_temp_dir} was not empty during cleanup. Manual check might be needed.")
        except OSError as e_rmdir:
            print(f"Error deleting request temp directory {request_specific_temp_dir}: {e_rmdir}")

    # Send the file and then schedule its cleanup
    try:
        return send_file(
            final_output_path,
            as_attachment=True,
            download_name='bulletproof_synthesized_audio.mp3',
            mimetype='audio/mpeg'
        )
    finally:
        # Cleanup the final concatenated file after sending
        # This might be tricky if send_file is asynchronous or streams;
        # for simple cases, it's often fine. For production, consider background task for cleanup.
        if os.path.exists(final_output_path):
            try:
                os.remove(final_output_path)
                print(f"Cleaned up final audio file: {final_output_path}")
            except OSError as e_final_clean:
                print(f"Error deleting final audio file {final_output_path}: {e_final_clean}")

if __name__ == '__main__':
    if not API_KEYS:
        print("--------------------------------------------------------------------")
        print("WARNING: GOOGLE_API_KEYS not found in .env or is empty.")
        print("The application will run in SIMULATED TTS mode.")
        print("Please create a .env file (copy .env.example) and add your keys.")
        print("--------------------------------------------------------------------")
    else:
        print(f"Loaded {len(API_KEYS)} API key(s). Application starting.")

    # Note: Using debug=True can cause ProcessPoolExecutor to behave unexpectedly on some OS (e.g. Windows)
    # or with some module reloading strategies. For production, debug=False is standard.
    # The launch scripts will run this directly, so debug mode might be less of an issue there.
    app.run(debug=True, host='0.0.0.0', port=5000)
