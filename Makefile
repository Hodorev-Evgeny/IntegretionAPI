include .env
export


app-run:
	uvicorn app.main:app --reload

deploy-build:
	@docker compose up -d --build

deploy-stop:
	@docker compose down