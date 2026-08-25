import re


def parse_timestamp_to_seconds(timestamp: str) -> float:
    """
    Converts a subtitle timestamp into seconds.
    Supports both SRT format (00:01:23,456) and VTT format (00:01:23.456).
    """
    timestamp = timestamp.strip()
    
    # Normalize: replace comma with dot (SRT uses comma, VTT uses dot)
    timestamp = timestamp.replace(",", ".")
    
    # Split into time and milliseconds
    parts = timestamp.split(".")
    milliseconds = 0
    if len(parts) > 1:
        milliseconds = int(parts[1].ljust(3, "0")[:3])
    
    time_part = parts[0]
    time_components = time_part.split(":")
    
    if len(time_components) == 3:
        hours = int(time_components[0])
        minutes = int(time_components[1])
        seconds = int(time_components[2])
    elif len(time_components) == 2:
        hours = 0
        minutes = int(time_components[0])
        seconds = int(time_components[1])
    else:
        hours = 0
        minutes = 0
        seconds = int(time_components[0])
    
    total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0
    return round(total_seconds, 3)


def strip_vtt_tags(text: str) -> str:
    """Removes VTT formatting tags like <c>, <i>, <b>, etc."""
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def parse_srt_content(content: str) -> list[dict]:
    """
    Parses SRT subtitle content into segments.
    
    SRT format:
    1
    00:00:01,000 --> 00:00:04,000
    Hello world
    """
    segments = []
    
    # Normalize line endings
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    
    # Split by blocks (separated by double newlines)
    blocks = re.split(r"\n\n+", content.strip())
    
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue
        
        # Line 0: index number (skip)
        # Line 1: timestamps
        timestamp_line = lines[1]
        
        if "-->" not in timestamp_line:
            continue
        
        try:
            start_str, end_str = timestamp_line.split("-->")
            start = parse_timestamp_to_seconds(start_str)
            end = parse_timestamp_to_seconds(end_str)
        except (ValueError, IndexError):
            continue
        
        # Lines 2+: text content
        text = " ".join(lines[2:]).strip()
        
        if text:
            segments.append({
                "start": start,
                "end": end,
                "text": text
            })
    
    return segments


def parse_vtt_content(content: str) -> list[dict]:
    """
    Parses VTT subtitle content into segments.
    
    VTT format:
    WEBVTT
    
    00:00:01.000 --> 00:00:04.000
    Hello world
    """
    segments = []
    
    # Normalize line endings
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    
    # Remove WEBVTT header and any metadata
    # Find the first timestamp line to skip headers
    lines = content.split("\n")
    
    # Find where the actual cues start (after WEBVTT header)
    cue_start_index = 0
    for i, line in enumerate(lines):
        if "-->" in line:
            # Go back to find the start of this cue block
            cue_start_index = max(0, i - 1)
            break
    
    # Rejoin from cue start
    cue_content = "\n".join(lines[cue_start_index:])
    
    # Split by blocks
    blocks = re.split(r"\n\n+", cue_content.strip())
    
    for block in blocks:
        block_lines = block.strip().split("\n")
        if len(block_lines) < 2:
            continue
        
        # Find the timestamp line in this block
        timestamp_line_index = -1
        for i, line in enumerate(block_lines):
            if "-->" in line:
                timestamp_line_index = i
                break
        
        if timestamp_line_index == -1:
            continue
        
        timestamp_line = block_lines[timestamp_line_index]
        
        # Remove cue settings (position:..., align:..., etc.)
        timestamp_part = timestamp_line.split("-->")
        if len(timestamp_part) < 2:
            continue
        
        try:
            start_str = timestamp_part[0].strip()
            end_str = timestamp_part[1].split(" ")[0].strip()  # Remove settings after end time
            
            start = parse_timestamp_to_seconds(start_str)
            end = parse_timestamp_to_seconds(end_str)
        except (ValueError, IndexError):
            continue
        
        # Text is everything after the timestamp line
        text_lines = block_lines[timestamp_line_index + 1:]
        text = " ".join(line.strip() for line in text_lines if line.strip())
        
        # Strip VTT tags
        text = strip_vtt_tags(text)
        
        if text:
            segments.append({
                "start": start,
                "end": end,
                "text": text
            })
    
    return segments


def parse_subtitle_content(content: str, filename: str) -> list[dict]:
    """
    Detects subtitle format and parses content.
    Returns a list of segment dictionaries.
    """
    if not content or not content.strip():
        raise ValueError("Subtitle file is empty.")
    
    filename_lower = filename.lower()
    
    if filename_lower.endswith(".srt"):
        return parse_srt_content(content)
    elif filename_lower.endswith(".vtt"):
        return parse_vtt_content(content)
    else:
        # Try to detect format from content
        if "WEBVTT" in content[:20]:
            return parse_vtt_content(content)
        else:
            return parse_srt_content(content)