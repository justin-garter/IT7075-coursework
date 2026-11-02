# RAG for Defense Contractor Compliance, Rebuilt with LangChain

IT7075C Applied AI for Cybersecurity, Mini Project 4. The same compliance question-and-answer bot as `../../module04/rag_project`, rebuilt with LangChain over the same five DFARS, CMMC and ITAR excerpts and the same eight questions (files are byte-identical). `TextLoader` and `CharacterTextSplitter` load and split the documents, `Chroma.from_documents` embeds them locally with `all-MiniLM-L6-v2` in cosine space, a `similarity_score_threshold` retriever keeps chunks scoring at or above a relevance threshold, and an LCEL chain pipes the retrieved context and question through a `ChatPromptTemplate` into `mistral:7b` on a loopback-only Ollama server. Each configuration is scored by answers found and refusals held while chunk size, k and the threshold are varied one at a time, with one row matching the RAG module's settings for a like-for-like comparison.

| File | Contents |
|---|---|
| `langchain_notebook.ipynb` | Practice pipeline (Parts 1 to 7) and the rebuilt compliance RAG (Part 8), saved with outputs |
| `my_kb/`, `goldset.json` | The same documents and questions as the RAG module |
| `results_langchain.csv` | One row per configuration tested; `like_for_like` marks the row matching the RAG module |
| `course_kb/`, `framework_goldset.json`, `results.csv` | Course knowledge base, questions and threshold sweep used in Parts 1 to 7 |

Run locally: `pip install langchain langchain-community langchain-chroma langchain-huggingface langchain-ollama sentence-transformers`, start Ollama with `mistral:7b` pulled, then run the notebook top to bottom from this folder.
