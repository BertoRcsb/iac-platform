SHELL := /usr/bin/env bash

TF ?= terraform
ENV ?= lab
TF_DIR := ../environments/$(ENV)

.PHONY: fmt init validate plan apply destroy lint sec verify check-env

check-env:
	@if [ ! -d "$(TF_DIR)" ]; then \
		echo "Environment not found: $(TF_DIR)"; \
		exit 1; \
	fi

fmt:
	@$(TF) fmt -recursive ..

init: check-env
	@cd "$(TF_DIR)" && $(TF) init

validate: check-env
	@cd "$(TF_DIR)" && $(TF) validate

plan: check-env
	@cd "$(TF_DIR)" && $(TF) plan

apply: check-env
	@cd "$(TF_DIR)" && $(TF) apply

destroy: check-env
	@cd "$(TF_DIR)" && $(TF) destroy

lint: check-env
	@if command -v tflint >/dev/null 2>&1; then \
		cd "$(TF_DIR)" && tflint --recursive; \
	else \
		echo "tflint not installed. Skipping lint."; \
	fi

sec:
	@if command -v trivy >/dev/null 2>&1; then \
		cd .. && trivy config .; \
	else \
		echo "trivy not installed. Skipping security scan."; \
	fi

verify: fmt init validate lint sec plan
