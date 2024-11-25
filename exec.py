import uvicorn


if __name__ == "__exec__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
