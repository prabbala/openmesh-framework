# Empirical-AiS Configuration Example

This example demonstrates how Empirical-AiS Inc. consumes the OpenMesh Framework.

## Overview

Empirical-AiS operates two products that use different observability adapters:

- **Plug-N-Play (PNP)** — Uses the `ServerAdapter` for EC2, Docker, Nginx, and Gunicorn health
- **Zero-Data-Vault (ZDV)** — Uses the `ServerlessAdapter` for Lambda, AppSync, DynamoDB, and KMS health

## 4-Tier Mapping

| Layer          | Value                             |
| -------------- | --------------------------------- |
| Entity         | Empirical-AiS Inc.                |
| Domain (LOB)   | AI Infrastructure / Cybersecurity |
| Product_Family | Plug-N-Play / Zero-Data-Vault     |
| Resource       | EC2 Instance / Lambda Function    |

## Usage

Place DomainRegistration YAML files in your project's `openmesh-config/domains/` directory and reference the appropriate adapter class.

See the framework documentation for the full adapter development guide.
