def split_text(
        text:str,
        chunk_size:int =200,
        overlap:int =30,
)->list[str]:
    """将长文本切分成多个有重叠的小片段."""
    if chunk_size <=0:
        raise ValueError('chunk_size must be > 0')
    if overlap<0 or overlap>=chunk_size:
        raise ValueError('overlap must be between 0 and chunk_size')
    chunks = []
    start = 0
    while start < len(text):
        end=start+chunk_size
        chunk=text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start+=chunk_size-overlap
    return chunks
