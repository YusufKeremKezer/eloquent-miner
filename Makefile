.PHONY: up install dev

up: install
	npm run dev

install:
	npm install

dev:
	npm run dev