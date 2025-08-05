import os 
import re

class MarkdownChunker:
    """
    A class to chunk a markdown file that contains multiple file contents.
    It combines smaller files into larger chunks to approximate the target
    chunk size, while splitting files that are larger than the chunk size.
    """

    def __init__(self, chunk_size=1024):
        """
        Initializes the MarkdownChunker.

        Args:
            chunk_size (int): The target maximum size of each chunk in characters.
        """
        if not isinstance(chunk_size, int) or chunk_size <= 0:
            raise ValueError("chunk_size must be a positive integer.")
        self.chunk_size = chunk_size

    def _split_large_file_body(self, header, body, chunks):
        """
        Helper method to split the body of a single large file into multiple chunks.
        Each resulting chunk will be smaller than self.chunk_size.
        """
        current_pos = 0
        while current_pos < len(body):
            # Calculate how much space is available for the body in a new chunk
            # after accounting for the header and formatting characters.
            available_space = self.chunk_size - (len(header) + 4) # 4 for "\n\n" * 2

            # Ensure we have a positive space to avoid infinite loops
            if available_space <= 0:
                # This case happens if the header itself is larger than the chunk size.
                # We truncate the header and add a note.
                truncated_header = header[:self.chunk_size - 50] + "..."
                chunks.append(f"{truncated_header}\n\n[Content omitted: header too large for chunk size]")
                return

            end_pos = current_pos + available_space
            
            # To avoid splitting mid-line, find the last newline before the end position.
            if end_pos < len(body):
                last_newline = body.rfind('\n', current_pos, end_pos)
                if last_newline > current_pos:
                    end_pos = last_newline
            
            chunk_body = body[current_pos:end_pos].strip()
            if chunk_body:
                chunks.append(f"{header}\n\n{chunk_body}")
            
            current_pos = end_pos

    def chunk_file(self, file_path):
        """
        Reads a markdown file and splits it into chunks.

        This method processes files sequentially, combining them into chunks that
        are close to `chunk_size` without exceeding it. If a single file's
        content is larger than `chunk_size`, it will be split across
        multiple chunks.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The file at {file_path} was not found.")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        file_header_pattern = r'\n# File: (.*?)\n'
        parts = re.split(file_header_pattern, content)
        
        all_files = []
        preamble = parts[0].strip()
        if preamble:
            all_files.append(("Unknown File (preamble)", preamble))

        file_paths = parts[1::2]
        file_bodies = parts[2::2]
        for i in range(len(file_paths)):
            all_files.append((file_paths[i].strip(), file_bodies[i].strip()))

        final_chunks = []
        current_chunk_content = ""

        for path, body in all_files:
            header = f"File: {path}"
            # Use a separator to distinguish files within the same chunk
            separator = "\n\n" + ("-" * 20) + "\n\n"
            file_block = f"{header}\n\n{body}"

            # Case 1: The file itself is larger than the chunk size.
            if len(file_block) > self.chunk_size:
                if current_chunk_content:
                    final_chunks.append(current_chunk_content)
                current_chunk_content = ""
                self._split_large_file_body(header, body, final_chunks)
                continue

            # Case 2: Adding the next file would make the chunk too big.
            # We add the separator length to the check.
            if current_chunk_content and (len(current_chunk_content) + len(separator) + len(file_block) > self.chunk_size):
                final_chunks.append(current_chunk_content)
                current_chunk_content = file_block
            # Case 3: The file fits.
            else:
                if not current_chunk_content:
                    current_chunk_content = file_block
                else:
                    current_chunk_content += separator + file_block
        
        # Add the last chunk if it exists
        if current_chunk_content:
            final_chunks.append(current_chunk_content)
            
        return final_chunks
