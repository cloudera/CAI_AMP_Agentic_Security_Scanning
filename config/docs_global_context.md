Guiding Principles
Audience First: All documentation must be written for three primary audiences:

New Developers: Need to understand the architecture and how to contribute.

Operators/DevOps: Need to know how to deploy, configure, and monitor the application.

API Consumers: Need to understand how to use the public-facing interfaces.

Action-Oriented and Practical: Prioritize "how-to" guides over long theoretical explanations. The primary goal is to enable users to accomplish tasks. The main README should contain everything a user needs to get the software running and perform its main function.

Documentation is Code: Treat documentation as a core part of the codebase. It must be version-controlled, reviewed, and updated alongside every code change. If the code changes, the documentation must change with it.

Single Source of Truth: The README.md is the central entry point. It should contain the most critical information and link to more detailed documents if necessary, but it must not be a placeholder. Avoid duplicating information that can be automatically generated or is better kept in code comments.

Required Sections for Final Report
The final documentation_report.md and the generated tickets.json must ensure the following topics are fully addressed in the suggested README.md:

High-Level Overview: A brief, clear explanation of what the project does and its primary use case.

Getting Started Guide: This section is mandatory. It must include:

Prerequisites: A list of all required tools.

Installation: How to install dependencies.

Running the Application: Clear instructions for both local development (e.g., make start) and production-like execution (e.g., docker run).

Running Tests: The exact command to execute the test suite (e.g., make test).

API Documentation: If the project exposes an API, it must be documented. Include:

The base URL.

A list of endpoints with HTTP methods (GET /users).

Example request payloads and successful response bodies.

Architectural Overview: A brief section explaining the primary modules or layers of the codebase to orient new developers.

Configuration: Explain any necessary environment variables or configurati