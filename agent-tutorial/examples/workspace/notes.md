# Workspace Researcher

This is a small teaching project for a research agent.

The model proposes actions. The host validates tool arguments, checks file
boundaries, and enforces explicit report-write permission.

The default model is scripted and offline. A live provider is optional.
Reports should distinguish facts from questions and refer to this document.

The program is not an operating-system sandbox. Third-party plugins would run
with the permissions of the Python process. Structure validation does not prove
the report's factual accuracy.
