import os
import whisper
from pydub import AudioSegment
import srt
from datetime import timedelta

def split_audio(input_audio_path, chunk_length_ms, chunks_folder):
    os.makedirs(chunks_folder, exist_ok=True)
    audio = AudioSegment.from_file(input_audio_path)
    chunks = []
    for i in range(0, len(audio), chunk_length_ms):
        chunk = audio[i:i + chunk_length_ms]
        chunk_name = f"{chunks_folder}/chunk_{i // chunk_length_ms}.wav"
        chunk.export(chunk_name, format="wav")
        chunks.append((chunk_name, i / 1000))  # store start time in seconds
    return chunks

def transcribe_chunks(chunks, model):
    full_text = ""
    subtitles = []
    for idx, (chunk_path, start_time) in enumerate(chunks):
        result = model.transcribe(chunk_path, task="translate")  # 🔄 Translate to English
        text = result["text"].strip()
        duration = AudioSegment.from_file(chunk_path).duration_seconds

        # Add transcription to full text
        full_text += f"{text} "

        # Add subtitle entry
        subtitle = srt.Subtitle(
            index=idx + 1,
            start=timedelta(seconds=start_time),
            end=timedelta(seconds=start_time + duration),
            content=text
        )
        subtitles.append(subtitle)

        print(f"✅ Processed chunk {idx + 1}/{len(chunks)}")

    return full_text, subtitles

def main():
    print("📂 Enter path to video/audio file (MP4, MP3, WAV, etc.):")
    input_path = input().strip()

    print("📄 Enter path to save transcription (e.g., output.txt):")
    output_text_path = input().strip()

    print("🎬 Enter path to save subtitles (e.g., output.srt):")
    output_srt_path = input().strip()

    print("⚡ Select Whisper model (tiny, base, small, medium, large):")
    model_name = input().strip()

    audio_path = "temp_audio.wav"
    chunks_folder = "audio_chunks"
    chunk_length_ms = 60 * 1000  # 1 minute per chunk

    # Extract audio from video
    print("🎙️ Extracting audio...")
    os.system(f"ffmpeg -i \"{input_path}\" -ac 1 -ar 16000 -f wav \"{audio_path}\" -y")

    # Split audio into chunks
    print("✂️ Splitting audio into chunks...")
    chunks = split_audio(audio_path, chunk_length_ms, chunks_folder)

    # Load Whisper and transcribe
    print(f"🔄 Loading Whisper model ({model_name})...")
    model = whisper.load_model(model_name)
    full_text, subtitles = transcribe_chunks(chunks, model)

    # Save transcription
    with open(output_text_path, "w", encoding="utf-8") as f:
        f.write(full_text.strip())
    print(f"✅ Transcription saved to: {output_text_path}")

    # Save subtitles
    with open(output_srt_path, "w", encoding="utf-8") as f:
        f.write(srt.compose(subtitles))
    print(f"✅ Subtitles saved to: {output_srt_path}")

    # Cleanup temp files
    os.remove(audio_path)
    for chunk_path, _ in chunks:
        os.remove(chunk_path)
    os.rmdir(chunks_folder)
    print("🧹 Cleanup complete.")

if __name__ == "__main__":
    main()