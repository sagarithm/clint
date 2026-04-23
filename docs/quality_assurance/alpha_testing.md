# Alpha Testing Guidelines

Alpha testing is conducted by developers during active release branches or staging phases. It focuses on safely routing real HTTP data without disrupting outbound channels. It is the final local check before real-world operator deployments.

## The "Dry Run" Paradigm
Because Clint V2 is an interactive messaging agent, executing commands like `clint worker x-threads --live-send` recklessly could cause irreversible domain reputation damage.

### Alpha Constraints
* Executed locally by developers running `uvicorn server:app` or `clint run` against the SQLite testing databases.
* LLM endpoints (`OpenRouter`) are hit natively to ensure API structures match expected `gemini` specs or OpenAI specs in `config.py`.
* Dispatching pipelines like Email MUST remain mocked or restricted strictly to `--dry-run` or internal developer testing addresses.

## Execution Vectors
1. Scrape maps targeting "Test Industry in Local Area".
2. Feed DB.
3. Validate API interactions natively pull real data.
4. Execute `engine` to test full LLM iteration parsing.
5. Watch Deadletter logic to ensure transient local network failures drop cleanly into the schema.
