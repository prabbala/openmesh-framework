# Sports-Avatar Configuration Example

This example demonstrates how Sports-Avatar LLC consumes the OpenMesh Framework.

## Overview

Sports-Avatar operates creative and streaming products that use specialized adapters:

- **Animation Engine** — Uses the `GPUAdapter` for Blender/Three.js GPU utilization and render pipeline health
- **Streaming Delivery** — Uses the `StreamingAdapter` for video and media streaming health

## 4-Tier Mapping

| Layer          | Value                     |
| -------------- | ------------------------- |
| Entity         | Sports-Avatar LLC         |
| Domain (LOB)   | Digital Humans            |
| Product_Family | Cric-Avatar               |
| Resource       | Blender Render Node / GPU |

## Usage

Place DomainRegistration YAML files in your project's `openmesh-config/domains/` directory and reference the appropriate adapter class.

See the framework documentation for the full adapter development guide.
