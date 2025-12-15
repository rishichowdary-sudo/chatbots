# Multi-agent Chatbot

## Setting up the environment

### 1. Create new environment and activate

```

python -m venv venv
source venv/Scripts/activate

```



### 2. Install requirements

```
pip install -r requirements.txt
```

### 3. Environment setup
Create a `.env` file within multi-agent chatbot folder. Add the following-

```
GOOGLE_API_KEY = <GOOGLE API KEY, if you are using google LLM>
COHERE_API_KEY = <COHERE KEY, if you are using Cohere LLM>
OPENAI_API_KEY = <OPENAI KEY, if you are using OpenAI LLM>

LANGCHAIN_TRACING_V2 = false <toggle to capture trace on LangSmith>
LANGCHAIN_ENDPOINT = https://api.smith.langchain.com
LANGCHAIN_API_KEY = < langchain api key >
LANGCHAIN_PROJECT = < langchain project name >

TAVILY_API_KEY = <TAVILY Web search key, required for conversation report app only>
App_SCREAT_KEY= <Secure login key for report app>

# IP from which traffic is to be allowed. 
# If running inside docker container have ALLOWED_IP = localhost:8000. 
# The IP given below is for local server.
ALLOWED_IP = '127.0.0.1:5000'
ALLOWED_DOMAIN = 'lollypop.design'

# key file for gcp storage, it should be of the format gcp*key.json to be gitignored
GOOGLE_APPLICATION_CREDENTIALS = 'gcp_tdsdev_backupschatbot_key.json'

# akamai storage details
LINODE_API_TOKEN = < linode api token >
LINODE_ACCESS_KEY = < linode access key >
LINODE_SECRET_KEY = < linode secret key >
```