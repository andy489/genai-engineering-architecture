# Basic RAG Query Engine - Step by Step

This project demonstrates how to build a **Retrieval-Augmented Generation (RAG) application** using vector search, help you understand and implement a basic RAG system step by step:

* Load and preprocess documents
* Generate embeddings
* Store vectors in a vector database
* Perform similarity search
* Augment LLM responses with retrieved context

---

[1]- Python installation
[2]- Create and activate a virtual Environment
[3]- Setup and Installation
[4]- Create API keys & set the environment variables 

### [1]-Python installation

#### macOS
1. **Check if Python is already installed**
   ```sh
   python3 --version
   ```
   If Python is not installed, proceed with the steps below.

2. **Install Homebrew (if not installed)**
   ```sh
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

3. **Install Python**
   ```sh
   brew install python3
   ```

4. **Check Python Version**
   ```sh
   python3 --version
   ```

#### Windows
1. **Download Python** from the official website: [https://www.python.org/downloads/](https://www.python.org/downloads/)

2. **Run the installer** and check the box **"Add Python to PATH"** before proceeding with the installation.

3. **Check Python Version**
   ```sh
   python --version
   ```

---

### [2]-Create and activate a virtual environment - [venv](https://docs.python.org/3/library/venv.html)

#### macOS
1. **Navigate to your project directory**
   ```sh
   cd /path/to/your/project
   ```

2. **Create a virtual environment**
   ```sh
   python3 -m venv .venv
   ```

3. **Activate the virtual environment**
   ```sh
   source .venv/bin/activate
   ```

4. **Verify that the virtual environment is active** (you should see `(venv)` in the terminal prompt).

#### Windows
1. **Navigate to your project directory**
   ```sh
   cd C:\path\to\your\project
   ```

2. **Create a virtual environment**
   ```sh
   python -m venv .venv
   ```

3. **Activate the virtual environment**
   ```sh
   .venv\Scripts\activate
   ```

4. **Verify that the virtual environment is active** (Command Prompt should show `(venv)` before the directory path).

---

## Deactivating the Virtual Environment
For both macOS and Windows, deactivate the virtual environment by running:
```sh
 deactivate
```

---

### [3]-Setup and Installation

**[wget](https://formulae.brew.sh/formula/wget)**

`wget` is a command-line tool used to download files from the web via HTTP, HTTPS, and FTP.

#### macOS Installation

* Using Homebrew (Recommended)

* Install Homebrew (if not already installed):

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

* Install `wget`

`brew install wget`

#### windows
* Using Chocolatey

```sh
Set-ExecutionPolicy Bypass -Scope Process -Force; `
[System.Net.ServicePointManager]::SecurityProtocol = `
[System.Net.ServicePointManager]::SecurityProtocol -bor 3072; `
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
```

* Install `wget`

`choco install wget`

---

Check Version

`wget --version`

---
Download Data 

```sh
!mkdir -p 'data/paul_graham/'
!wget 'https://raw.githubusercontent.com/run-llama/llama_index/main/docs/examples/data/paul_graham/paul_graham_essay.txt' -O 'data/paul_graham/paul_graham_essay.txt'

!wget 'https://github.com/run-llama/llama_index/blob/main/docs/examples/data/paul_graham/paul_graham_essay_ambiguated.txt' -O 'data/paul_graham/paul_graham_essay-ambiguated.txt'
```

(Mac)
```sh
pip3 install -r requirements.txt
```

(Windows)
```sh
pip install -r requirements.txt
```

---

## Exiting the Virtual Environment
Simply run:
```sh
deactivate
```

### [4]-Create API keys & set the environment variables 


#### 4.1 Setting Up OpenAI Secret Key  
1. Create an OpenAI Account[OpenAI's API Keys page](https://platform.openai.com/signup/),
2. Go to [OpenAI's API Keys page](https://platform.openai.com/settings/organization/api-keys),
3. Click **Create new secret key** and copy it, 
4. You will need to add your billing information (MANAGE > Settings > Billing).  


#### 4.2 LangSmith
1. Create a [LangSmith Account](https://smith.langchain.com/),
2. Select **Tracing** from the sidebar menu and **Create a new project**


#### Set environment variables 

##### macOS & Linux  
You can store the key in your shell configuration file:  

```sh
echo 'export OPENAI_API_KEY="your-secret-key"' >> ~/.bashrc
source ~/.bashrc
````

or add to `.env` file (update the `.env.example` file)

```sh
OPENAI_API_KEY="YOUR_OPENAI_API_KEY_H"
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY="YOUR_LANGSMITH_API_KEY"
LANGSMITH_PROJECT="PROJECT_NAME"

```




