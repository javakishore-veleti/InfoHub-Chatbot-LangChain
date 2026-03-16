# Workflow Name 01 - AWS Bedrock Doc Guide

 "workflow_id": "ingest_001",
 display_name": "AWS Bedrock Docs Ingest",
 "short_description": "Crawl AWS Bedrock docs and generate multi-strategy chunks for retrieval.",
 "seed_url": "https://docs.aws.amazon.com/bedrock/latest/userguide/what-is-bedrock.html",

# Input
AWS Bedrock documentation URL: https://docs.aws.amazon.com/bedrock/latest/userguide/what-is-bedrock.html

# Workflow Activities:

## Activity 01 - Fetch AWS Bedrock Documentation
1. Read the content from the provided AWS Bedrock documentation URL.
2. Apply 6 chunking strategies to break down the content into manageable pieces:
   - Strategy 1: Fixed-Sized token chunking: simple blocks by token count; fast baseline method.
     - Example: Split the document into chunks of 500 tokens each.
   - Strategy 2: Sliding window with overlap: create chunks with overlapping content to preserve context.
     - Example: Create chunks of 500 tokens with a 100-token overlap between consecutive chunks.
   - Strategy 3:Sentence based chunking. Split the document into chunks based on sentence boundaries, ensuring that each chunk contains complete sentences.
     - Example: Use a natural language processing library to identify sentence boundaries and create chunks that contain whole sentences, with a maximum of 500 tokens per chunk.
   - Strategy 4: Semantic chunking. Use semantic understanding to create chunks based on topics or sections within the document.
     - Example: Analyze the document structure and content to identify logical sections (e.g., introduction, features, use cases) and create chunks that correspond to these sections, ensuring that each chunk is coherent and focused on a specific topic.
    - Strategy 5: Hierarchical Chunking. Combine multiple chunking strategies to create a hierarchical structure of chunks, allowing for both broad and detailed analysis of the document.
      - Example: First, use semantic chunking to identify major sections of the document, then apply fixed-sized token chunking within each section to create smaller, manageable chunks for detailed analysis.
    - Strategy 6: Query-aware chunking. Create chunks based on anticipated user queries or information needs, ensuring that each chunk is relevant to specific questions or topics.
      - Example: Analyze common user queries related to AWS Bedrock and create chunks that are tailored to answer those queries, such as chunks focused on features, pricing, or use cases.


## Activity 02 -

## Workflow Requirements:
- Ensure the workflow tasks for each chunking strategy is reusable so define a module workflows/Common/Tasks/<all chunking strategies python classes>
- workflows/data_load/ingest_wf_facade.py acts as a facade for all ingest workflows.
    - This reads config.json and understands the workflow configurations and sequence of tasks and invokes them accordingly.
- Each chunking strategy should be implemented as a separate class in the Common/Tasks directory

## Exception Handling:
1. Ensure exceptions during specific chunking strategy is property recorded in the execution details workflow instance data either in the database or in the execution metadata file that is created for every workflow execution
2. Show this exception at high level in the UI