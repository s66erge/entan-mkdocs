import tiktoken
import sys

def count_tokens_file(file_path: str, encoding_name: str = "cl100k_base") -> int:
    encoding = tiktoken.get_encoding(encoding_name)
    with open(file_path, 'r', encoding='utf-8') as f:  # Handles Windows line endings
        text = f.read()
    return len(encoding.encode(text))

if __name__ == "__main__":
    file_path = sys.argv[1] if len(sys.argv) > 1 else "test.txt"
    tokens = count_tokens_file(file_path)
    print(f"Tokens in {file_path}: {tokens}")
