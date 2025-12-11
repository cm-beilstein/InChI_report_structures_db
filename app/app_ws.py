
import os
import uvicorn
import logging

# from a2wsgi import WSGIMiddleware
from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse

from db_model import Issues, get_session

app = FastAPI()

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
    try:
        verify_token(request)
    except Exception as e:
        return JSONResponse(status_code=401, content={"error": str(e)})
    return {"status": "ok"}

@app.post("/ingest_issue")
async def ingest_issue(request: Request, session=Depends(get_session)):
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
        return JSONResponse(status_code=400, content={"error": str(ve)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# Route to get all issues sorted by date
@app.get("/get_all_issues")
async def get_issues(request: Request, session=Depends(get_session)):
    
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
    
    uvicorn.run(
        "app_ws:app",
        host='0.0.0.0', 
        port=gui_port,     
        ssl_keyfile="server.key",
        ssl_certfile="server.crt"
        # dev_tools_silence_routes_logging=False 
    )
    