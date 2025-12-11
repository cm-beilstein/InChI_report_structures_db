
import os
import uvicorn
import logging

# from a2wsgi import WSGIMiddleware
from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse

from db_model import Issues, get_session, init_db

app = FastAPI()

token_check_enabled = True

# Load tokens from file
def load_tokens():
    token_file = os.environ.get("INCHI_TOKENS_FILE", "tokens.txt")
    if os.path.exists(token_file):
        with open(token_file, 'r') as f:
            return set(line.strip() for line in f if line.strip())
    return {}

def verify_token(request: Request):    
    token = request.headers.get("Authorization")
    all_tokens = load_tokens()
    if token not in all_tokens:
        raise Exception("Invalid or missing token")
    
@app.get("/health")
async def health_check(request: Request):
    if token_check_enabled:
        try:
            verify_token(request)
        except Exception as e:
            return JSONResponse(status_code=401, content={"error": str(e)})
    
    return JSONResponse(status_code=200, content={"status": "success"})

@app.get("/db_check")
async def db_check(request: Request):
    try:
        # Try to get a session and execute a simple query
        db_check_status, error_messge = Issues.check_connection()
        if db_check_status:
            return JSONResponse(status_code=200, content={"db_status": "connected"})
        else:
            return JSONResponse(status_code=500, content={"db_status": "error", "details": error_messge})    
    except Exception as e:
        return JSONResponse(status_code=500, content={"db_status": "error", "details": str(e)})

@app.post("/ingest_issue")
async def ingest_issue(request: Request, session=Depends(get_session)):
    if token_check_enabled:
        try:
            verify_token(request)
        except Exception as e:
            return JSONResponse(status_code=401, content={"error": str(e)})
            
    try:
        if request is None:
            raise ValueError
        data = await request.json()    
        issue = Issues.add(session, **data)
        return JSONResponse(content={"status": "success", "issue_id": issue.id})
    except ValueError as ve:
        try:
            example_str = Issues.example_json()
        except Exception as ex2:
            print("shit")

        return JSONResponse(status_code=400, content={"error": str(ve) + " example: " + example_str})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/get_nof_issues")
async def get_issues(request: Request, session=Depends(get_session)):

    if token_check_enabled:
        try:
            verify_token(request)
        except Exception as e:
            return JSONResponse(status_code=401, content={"error": str(e)})

    nof_issues = Issues.get_nof_issues(session)

    return JSONResponse(content={"nof_issues": nof_issues})

@app.get("/get_all_issues")
async def get_issues(request: Request, session=Depends(get_session)):
    
    if token_check_enabled:
        try:
            verify_token(request)
        except Exception as e:
            return JSONResponse(status_code=401, content={"error": str(e)})
    
    issues = Issues.get_all_sorted_by_date(session)
    # Convert SQLAlchemy objects to dicts
    result = [
        {
            "id": issue.id,
            "user": issue.user,
            "description": issue.description,
            "date_created": str(issue.date_created),
            "molfile": issue.molfile,
            "inchi": issue.inchi,
            "auxinfo": issue.auxinfo,
            "inchikey": issue.inchikey,
            "logs": issue.logs,
            "options": issue.options,
            "inchi_version": issue.inchi_version
        }
        for issue in issues
    ]
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
    