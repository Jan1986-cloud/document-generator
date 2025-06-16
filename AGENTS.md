# Contributor Guide for AI Agent

## Project Overview
This repository contains a document generator application with a Python/Flask backend and a React/Vite frontend.

- Backend source code is in `document-generator-backend/`.
- Frontend source code is in `document-generator-frontend/`.
- Infrastructure as Code is in `terraform/`.

## Development Environment
- The frontend uses `pnpm` for package management.
- Before running any frontend tasks, you must run `pnpm install` in the `document-generator-frontend` directory.

## Testing and Validation
- To validate frontend changes, run `pnpm run build` from the `document-generator-frontend` directory. This command must complete without errors.
- To validate backend changes, refer to the CI plan in `.github/workflows/deploy.yml`.

## Pull Request Instructions
- PR titles should be descriptive of the change.
- PR body should include a summary of the changes and how to test them.