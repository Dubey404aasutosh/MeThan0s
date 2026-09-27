"""
Server launcher for METHANOS Priority Engine API.
Starts uvicorn development server on http://localhost:8000
"""

import uvicorn

if __name__ == "__main__":
    print("==================================================================")
    print("   METHANOS — City Gas Distribution Network Priority Engine     ")
    print("   API Running at: http://localhost:8000                          ")
    print("   API Documentation (Swagger UI): http://localhost:8000/docs     ")
    print("==================================================================")
    uvicorn.run("priority_engine.api:app", host="0.0.0.0", port=8000, reload=True)
