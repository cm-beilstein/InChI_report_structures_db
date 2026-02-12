
import os
import uvicorn
import logging
import json
import inspect

# from a2wsgi import WSGIMiddleware
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from db_model import Issues, Issue_in, get_session, init_db
from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI()

main_app = FastAPI()
main_app.mount("/report", app)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        logger = logging.getLogger("app.access")
        logger.info(f"Request: {request.method} {request.url.path}")
        response = await call_next(request)
        logger.info(f"Response: {request.method} {request.url.path} - Status {response.status_code}")
        return response

app.add_middleware(LoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

token_check_enabled = True

# Load tokens from file
def load_tokens():
    token_file = os.environ.get("INCHI_TOKENS_FILE")
    if os.path.exists(token_file):
        with open(token_file, 'r') as f:
            return json.load(f)
    return {}

def is_token_valid(token: str, used_function: str):
            
    all_tokens_dict = load_tokens()
    
    allowed_functions = all_tokens_dict.get(token, [])
    if "all" in allowed_functions:
        return True
    elif used_function in allowed_functions:
        return True
        
    return False
        
@app.get("/health")
async def health_check():
    try:
        return JSONResponse(status_code=200, content={"status": "success"})
    except Exception as ex:
        return JSONResponse(status_code=500, content={"db_status": "error", "details": str(ex)})

@app.get("/db_check")
async def db_check(token: str):
    
    if token_check_enabled:
        if not is_token_valid(token, inspect.currentframe().f_code.co_name):
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
async def ingest_issue(token: str, issue: Issue_in, session=Depends(get_session)):
    if token_check_enabled:
        if not is_token_valid(token, inspect.currentframe().f_code.co_name):
            return JSONResponse(status_code=401, content={"error": 'Token invalid or missing'})
            
    try:
        data = issue.model_dump(exclude_unset=True)

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
        if not is_token_valid(token, inspect.currentframe().f_code.co_name):
            return JSONResponse(status_code=401, content={"error": 'Token invalid or missing'})

    nof_issues = Issues.get_nof_issues(session)

    return JSONResponse(content={"nof_issues": nof_issues})

@app.get("/get_all_issues")
async def get_all_issues(token: str, session=Depends(get_session)):
    
    if token_check_enabled:
        if not is_token_valid(token, inspect.currentframe().f_code.co_name):
            return JSONResponse(status_code=401, content={"error": 'Token invalid or missing'})
    
    issues = Issues.get_all_sorted_by_date(session)
    
    result = [Issues.to_dict(issue) for issue in issues]

    return JSONResponse(content={"issues": result})

if __name__ == "__main__":    
    logging.basicConfig(
        level=logging.INFO,
        filename="/app/logs/app.log",  # Log file path
        filemode="a",        # Append mode
        format="%(asctime)s %(levelname)s %(name)s %(message)s"        
    )
    
    log = logging.getLogger(__name__)
    log.setLevel(logging.INFO)

    gui_port = int(os.environ.get("INCHI_WS_APP_PORT", 8612)) 

    if init_db():        
        uvicorn.run(
            "app_ws:main_app",
            host='0.0.0.0', 
            port=gui_port,     
            # ssl_keyfile="server.key",
            # ssl_certfile="server.crt"
            # dev_tools_silence_routes_logging=False 
        )
    else:
        print("No db?")
    