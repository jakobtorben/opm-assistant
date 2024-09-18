# OPM Assistant

This is a chatbot application that uses RAG (Retrieval-Augmented Generation) to answer questions about the OPM reservoir simulator.

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv opm_assistant_venv
   ```
3. Activate the virtual environment:
   - Windows: `opm_assistant_venv\Scripts\activate`
   - macOS/Linux: `source opm_assistant_venv/bin/activate`
4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
5. Create a `.env` file in the root directory and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Running the App

1. Ensure your virtual environment is activated
2. Run the Streamlit app:
   ```
   streamlit run app.py
   ```
3. Open the provided URL in your web browser

## Note

Make sure you have the necessary data in the `./chroma_langchain_db` directory for the vector store to function properly.