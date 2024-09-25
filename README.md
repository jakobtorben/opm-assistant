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
5. Optionally, for local testing, create a `.env` file in the root directory and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Running the App

### Option 1: Local Setup

1. Ensure your virtual environment is activated
2. Run the Streamlit app:
   ```
   streamlit run app.py
   ```
3. Open the provided URL in your web browser

### Option 2: Docker Container

1. Build the Docker image:
   ```
   docker build -t opm-assistant .
   ```
2. Run the Docker container:
   ```
   docker run -p 8501:8501 opm-assistant
   ```
3. Optionally, for local testing, create a `.env` file in the root directory and add your OpenAI API key:
   ```
   docker run -p 8501:8501 -e OPENAI_API_KEY=your_api_key_here opm-assistant
   ```

3. Open `http://localhost:8501` in your web browser
