# Multi-agent Chatbot

## Setting up the environment

### 1. Create new environment and activate

Virtual Environment:
```
python -m venv venv
source venv/Scripts/activate

```

Conda Environment:
```
conda create -n env_name python=version
conda activate env_name

```



### 2. Install requirements

```
pip install -r requirements.txt
```

### 3. Run the following once to create knowledge base for FAQs and RAG

#### FAQ Embeddings creation from pdf document and Vectorstore creation for RAG Agent:
1. Create '<company_name>/faq_data' folder inside 'Data' folder. 
2. Place your FAQ pdf file in this folder. 
3. Update the client_properties.yaml file with necessary details.
4. From 'multi-agent-chatbot' directory run the following command:
```
python src/setup.py -n <company_name>
```

