# AI Architecture
AI Gateway → permission filter → patient-context retrieval → model provider → safety/validation layer → draft → clinician approval → audit log.
Use provider abstraction so models can be changed without rewriting clinical workflows.
