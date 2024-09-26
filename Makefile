format:
	poetry run black bot
	poetry run isort bot

lint:
	poetry run pylint bot