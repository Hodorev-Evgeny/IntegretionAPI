include .env
export


app-run:
	uvicorn app.main:app --reload
