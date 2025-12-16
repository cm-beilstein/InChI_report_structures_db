
import os
import uvicorn
import logging
import base64

# from a2wsgi import WSGIMiddleware
from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from typing import Optional
from db_model import Issues, Issue_in, get_session, init_db
from helper_util import is_base64_encoded

app = FastAPI()

token_check_enabled = True

# Load tokens from file
def load_tokens():
    token_file = os.environ.get("INCHI_TOKENS_FILE", "tokens.txt")
    if os.path.exists(token_file):
        with open(token_file, 'r') as f:
            return set(line.strip() for line in f if line.strip())
    return {}

def is_token_valid(token: str):
    all_tokens = load_tokens()
    return token in all_tokens
        
    
@app.get("/health")
async def health_check():
    try:
        return JSONResponse(status_code=200, content={"status": "success"})
    except Exception as ex:
        return JSONResponse(status_code=500, content={"db_status": "error", "details": str(ex)})

@app.get("/db_check")
async def db_check(token: str):
    
    if token_check_enabled:
        if not is_token_valid(token):
            return JSONResponse(status_code=401, content={"error": 'Token invalid or missing'})
            
    try:
        # Try to get a session and execute a simple query
        db_check_status, error_messge = Issues.check_connection()
        if db_check_status:
            return JSONResponse(status_code=200, content={"db_status": "connected"})
        else:
            return JSONResponse(status_code=500, content={"db_status": "error", "details": error_messge})    
    except Exception as ex:
        return JSONResponse(status_code=500, content={"db_status": "error", "details": str(ex)})

@app.post("/ingest_issue")
async def ingest_issue(token: str, issue: Issue_in, request: Request, session=Depends(get_session)):
    if token_check_enabled:
        if not is_token_valid(token):
            return JSONResponse(status_code=401, content={"error": 'Token invalid or missing'})
            
    try:
        data = issue.model_dump(exclude_unset=True)
        if "molfile" in data and data["molfile"] is not None:
            if isinstance(data["molfile"], str):
                # If it's a plain string (not base64), encode to bytes and then base64 encode
                try:
                    if is_base64_encoded(data["molfile"]):
                        data["molfile"] = data["molfile"].encode('utf-8')
                    else:
                        print("is string: encoding", data["molfile"])
                        data["molfile"] = base64.b64encode(data["molfile"].encode('utf-8'))

                    # Try to decode as base64 first (if already encoded, this will succeed)
                    # print("test1", data["molfile"])
                    # print("test2", data["molfile"].encode('utf-8'))
                    # print("test3", base64.b64decode(data["molfile"]))
                    # print("test4", base64.b64encode(data["molfile"].encode('utf-8')))
                    # print("test5", base64.b64encode(data["molfile"].encode('utf-8')).decode('utf-8'))
                    # print("test6", is_base64_encoded(data["molfile"]))
                    # # base64.b64decode(data["molfile"])
                    # print("test5")
                except Exception:
                    # If decoding fails, treat as plain string and encode
                    # data["molfile"] = base64.b64encode(data["molfile"].encode('utf-8'))
                    print("failed")

        issue_obj = Issues.add(session, **data)
        return JSONResponse(content={"status": "success", "issue_id": issue_obj.id})
                        
    except ValueError as ve:
        try:
            example_str = Issues.example_json()
        except Exception as ex2:
            example_str = ""
        return JSONResponse(status_code=400, content={"error": str(ve) + " example: " + example_str})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/get_nof_issues")
async def get_nof_issues(token: str, session=Depends(get_session)):

    if token_check_enabled:
        if not is_token_valid(token):
            return JSONResponse(status_code=401, content={"error": 'Token invalid or missing'})

    nof_issues = Issues.get_nof_issues(session)

    return JSONResponse(content={"nof_issues": nof_issues})

@app.get("/get_all_issues")
async def get_all_issues(token: str, get_molfile_as_string : Optional[bool] = False, session=Depends(get_session)):
    
    if token_check_enabled:
        if not is_token_valid(token):
            return JSONResponse(status_code=401, content={"error": 'Token invalid or missing'})
    
    issues = Issues.get_all_sorted_by_date(session)
    
    result = [Issues.to_dict(issue, get_molfile_as_string) for issue in issues]

    return JSONResponse(content={"issues": result})

if __name__ == "__main__":    
    logging.basicConfig(level=logging.INFO)
    
    log = logging.getLogger(__name__)
    log.setLevel(logging.INFO)

    gui_port = int(os.environ.get("INCHI_WS_APP_PORT", 8612)) 

    if init_db():        
        uvicorn.run(
            "app_ws:app",
            host='0.0.0.0', 
            port=gui_port,     
            ssl_keyfile="server.key",
            ssl_certfile="server.crt"
            # dev_tools_silence_routes_logging=False 
        )
    else:
        print("No db?")
    