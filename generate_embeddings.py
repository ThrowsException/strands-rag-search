from textwrap import wrap
import chromadb
import ollama
import os
import json
from pathlib import Path
from markitdown import MarkItDown
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize clients
chroma_client = chromadb.HttpClient(host='localhost', port=8000)

# Initialize markdown converter
md_converter = MarkItDown()


def discover_html_files(html_downloads_dir: str = "html_downloads") -> list[Path]:
    """Discover all HTML files in the downloads directory"""
    html_files = []
    downloads_path = Path(html_downloads_dir)
    
    if not downloads_path.exists():
        logger.error(f"HTML downloads directory not found: {downloads_path}")
        return html_files
    
    # Recursively find all .html files
    for html_file in downloads_path.rglob("*.html"):
        html_files.append(html_file)
        
    logger.info(f"Found {len(html_files)} HTML files")
    return html_files


def load_url_mapping(html_downloads_dir: str = "html_downloads") -> dict:
    """Load the URL mapping file if it exists"""
    mapping_file = Path(html_downloads_dir) / "url_mapping.json"
    
    if mapping_file.exists():
        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                url_mapping = json.load(f)
            logger.info(f"Loaded URL mapping with {len(url_mapping)} entries")
            return url_mapping
        except Exception as e:
            logger.error(f"Failed to load URL mapping: {e}")
    else:
        logger.warning("No URL mapping file found")
        
    return {}


def convert_html_to_markdown(html_file: Path) -> str:
    """Convert HTML file to markdown text"""
    try:
        # Read HTML content
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Convert to markdown using markitdown
        result = md_converter.convert(html_content)
        markdown_text = result.text_content if hasattr(result, 'text_content') else str(result)
        
        return markdown_text
        
    except Exception as e:
        logger.error(f"Failed to convert {html_file} to markdown: {e}")
        return ""


def generate_embedding(text: str, model: str = "nomic-embed-text:latest") -> list[float]:
    """Generate embedding for text using Ollama"""
    try:
        response = ollama.embed(
            model=model,
            input=text
        )
        return response['embedding']
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        return []


def process_html_file(html_file: Path, url_mapping: dict) -> dict:
    """Process a single HTML file and extract metadata"""
    logger.info(f"Processing: {html_file}")
    
    # Get file info
    stats = html_file.stat()
    
    # Find corresponding URL from mapping
    original_url = None
    title = None
    timestamp = None
    
    for url, info in url_mapping.items():
        if info.get('local_file_path') == str(html_file):
            original_url = url
            title = info.get('title', '')
            timestamp = info.get('timestamp', '')
            break
    
    # Convert to markdown
    markdown_content = convert_html_to_markdown(html_file)
    
    # Prepare document metadata
    metadata = {
        'file_path': str(html_file),
        'filename': html_file.name,
        'domain': html_file.parent.name,
        'size_bytes': stats.st_size,
        'original_url': original_url or str(html_file),
        'title': title or html_file.stem,
        'timestamp': timestamp,
        'content_length': len(markdown_content)
    }
    
    return {
        'content': markdown_content,
        'metadata': metadata
    }


def create_or_get_collection(collection_name: str = "html_documents"):
    """Create or get ChromaDB collection"""
    try:
        # Try to get existing collection
        collection = chroma_client.get_collection(name=collection_name)
        logger.info(f"Using existing collection: {collection_name}")
    except Exception:
        # Create new collection
        collection = chroma_client.create_collection(name=collection_name)
        logger.info(f"Created new collection: {collection_name}")
    
    return collection


def add_documents_to_collection(documents: list[dict], collection, batch_size: int = 10):
    """Add documents to ChromaDB collection in batches"""
    total_docs = len(documents)
    logger.info(f"Adding {total_docs} documents to collection in batches of {batch_size}")
    
    for i in range(0, total_docs, batch_size):
        batch = documents[i:i + batch_size]
        
        # Prepare batch data
        ids = []
        documents_content = []
        embeddings = []
        metadatas = []
        
        for j, doc in enumerate(batch):
            doc_id = f"doc_{i + j}"
            content = doc['content']
            metadata = doc['metadata']
            
            # Skip empty documents
            if not content.strip():
                logger.warning(f"Skipping empty document: {metadata.get('filename', 'unknown')}")
                continue
            
            # Generate embedding
            logger.info(f"Generating embedding for: {metadata.get('filename', 'unknown')}")
            embedding = generate_embedding(content)
            
            if not embedding:
                logger.warning(f"Failed to generate embedding for: {metadata.get('filename', 'unknown')}")
                continue
            
            ids.append(doc_id)
            documents_content.append(content)
            embeddings.append(embedding)
            metadatas.append(metadata)
        
        # Add batch to collection
        if ids:
            try:
                collection.add(
                    ids=ids,
                    documents=documents_content,
                    embeddings=embeddings,
                    metadatas=metadatas
                )
                logger.info(f"Added batch {i//batch_size + 1}/{(total_docs + batch_size - 1)//batch_size} ({len(ids)} documents)")
            except Exception as e:
                logger.error(f"Failed to add batch to collection: {e}")


def main():
    """Main function to process HTML files and generate embeddings"""
    logger.info("Starting HTML files processing for embeddings generation...")
    
    collection = create_or_get_collection()

    html_file_path = Path("./html_downloads/ibx.com")
    print(html_file_path)
    
    for html_file in html_file_path.rglob("*.html"):
        md = md_converter.convert(html_file)
        print(f"Processing {html_file.stem}")
        
        # Split content into 500 character chunks
        chunks = wrap(md.text_content, width=500, break_long_words=False, break_on_hyphens=False)
        
        # Process each chunk
        for i, chunk in enumerate(chunks):
            if chunk.strip():  # Skip empty chunks
                chunk_id = f"{html_file.stem}_chunk_{i}"
                print(f"  Chunk {i}: {chunk[:100]}...")
                
                collection.add(
                    ids=[chunk_id],
                    documents=[chunk],
                    metadatas=[{
                        'filename': html_file.name,
                        'chunk_index': i,
                        'total_chunks': len(chunks),
                        'chunk_size': len(chunk)
                    }]
                )
            
      
    
    # # Load URL mapping
    # url_mapping = load_url_mapping()
    
    # # Discover HTML files
    # html_files = discover_html_files('html_downloads/ibx.com')
    
    # if not html_files:
    #     logger.warning("No HTML files found to process")
    #     return
    
    # # Process all HTML files
    # documents = []
    # for html_file in html_files:
    #     try:
    #         doc_data = process_html_file(html_file, url_mapping)
    #         if doc_data['content'].strip():  # Only add non-empty documents
    #             documents.append(doc_data)
    #     except Exception as e:
    #         logger.error(f"Failed to process {html_file}: {e}")
    
    # logger.info(f"Processed {len(documents)} documents successfully")
    
    # if not documents:
    #     logger.warning("No valid documents to add to collection")
    #     return
    
    # # Create or get ChromaDB collection
    # collection = create_or_get_collection()
    
    # # Add documents to collection
    # add_documents_to_collection(documents, collection)
    
    # logger.info("Embeddings generation complete!")
    
    # # Print summary
    # print(f"\nSummary:")
    # print(f"- Processed {len(html_files)} HTML files")
    # print(f"- Generated embeddings for {len(documents)} documents")
    # print(f"- Collection: html_documents")
    # print(f"- Total content: {sum(len(doc['content']) for doc in documents):,} characters")


if __name__ == "__main__":
    main()