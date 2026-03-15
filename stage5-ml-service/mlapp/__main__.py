import uvicorn

uvicorn.run("mlapp.server:app", host="0.0.0.0", port=8000)
