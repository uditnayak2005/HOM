# HOM
## Install Dependencies:  
    pip install fastapi uvicorn python-multipart pyjwt


Run **"api_hom.py"** in terminal
And 
## In the same terminal, use Uvicorn to run the application: 
    uvicorn api_hom:app --reload

### Once Uvicorn starts, your API will be start at [http://127.0.0.1:8000] 

## Use CURL
### Get a Token (Authentication)
    curl -X POST -F username=testuser -F password=1@TESTPASS http://127.0.0.1:8000/Token
### Get Tasks (with Authorization)
    curl -X GET -H "Authorization: Bearer 1@Uditnayak" http://127.0.0.1:8000/Tasks/
