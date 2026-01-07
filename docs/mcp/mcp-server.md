# MCP server

## Collections

* [py-mcp-collection](https://github.com/strawgate/py-mcp-collection)
  MCP Oops, Filesystem Operations, Local References
* [reference implementations](https://github.com/modelcontextprotocol/servers/)
  + Everything - Reference / test server with prompts, resources, and tools
  + Fetch - Web content fetching and conversion for efficient LLM usage
  + Filesystem - Secure file operations with configurable access controls
  + Git - Tools to read, search, and manipulate Git repositories
  + Memory - Knowledge graph-based persistent memory system
  + Sequential Thinking - Dynamic and reflective problem-solving through thought sequences
  + Time - Time and timezone
  + and many third-party servers

## Uncategorised

* [Sequential Thinking MCP Server](https://github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking)
  dynamic and reflective problem-solving through a structured thinking process

## Special Apps

* [linkwarden](https://github.com/irfansofyana/linkwarden-mcp-server)

## Browser

ATTENTION:
For security reasons, always use a special profile (of the browser) for browser MCPs!

### Chrome

* [chrome-mcp](https://github.com/lxe/chrome-mcp)
  + only URLs, test and tabs, no debug
  + limited
* [mcp-chrome](https://github.com/hangwin/mcp-chrome?tab=readme-ov-file) featured!
  + supports stdout with special configuration
  + full fledged
  + working
  + extremely long tools list, hence not listed here
* [browser-tools-mcp](https://github.com/AgentDeskAI/browser-tools-mcp)
  + full fledged (?)
  + https://browsertools.agentdesk.ai/installation

### Firefox

* [browser-control-mcp](https://github.com/vpsone/browser-control-mcp)
  + only URLs, test and tabs, no debug
  + limited - but working

#### browser-control-mcp

* open-browser-tab
  + Open a new tab in the user's browser
* close-browser-tabs
  + Close tabs in the user's browser by tab IDs
* get-list-of-open-tabs
  + Get the list of open tabs in the user's browser
* get-recent-browser-history
  + Get the list of recent browser history (to get all, don't use searchQuery)
* get-tab-web-content
  + Get the full text content of the webpage and the list of links in the webpage, by tab ID
* reorder-browser-tabs
  + Change the order of open browser tabs
* find-highlight-in-browser-tab
  + Find and highlight text in a browser tab

### Playwright

* [playwright-mcp](https://github.com/microsoft/playwright-mcp)
  + firefox or chrome
  + browser testing
  + working

* extremely long tools list, hence not listed here

## DBs

### SQLite3

#### sqlite-explorer-fastmcp-mcp-server

* [sqlite-explorer-fastmcp-mcp-server](https://github.com/hannesrudolph/sqlite-explorer-fastmcp-mcp-server)

## dev containers

### mcp-devcontainers - working

* [mcp-devcontainers](https://github.com/crunchloop/mcp-devcontainers)

* devcontainer_up
  + Start or initialize a devcontainer environment in the specified workspace folder.Use this to ensure the devcontainer is running and ready for development tasks.
* devcontainer_run_user_commands
  + Run the user-defined postCreateCommand and postStartCommand scripts in the devcontainerfor the specified workspace folder. Use this to execute setup or initialization commandsafter the devcontainer starts.
* devcontainer_exec
  + Execute an arbitrary shell command inside the devcontainer for the specified workspace folder.Use this to run custom commands or scripts within the

## (local) filesystem

### @modelcontextprotocol/filesystem - working

* [@modelcontextprotocol/filesystem](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem)
  + path could be limited

* read_file
  + Read the complete contents of a file from the file system. Handles various text encodings and provides detailed error messages if the file cannot be read. Use this tool when you need to examine the contents of a single file. Use the 'head' parameter to read only the first N lines of a file, or the 'tail' parameter to read only the last N lines of a file. Only works within allowed directories.
* read_multiple_files
  + Read the contents of multiple files simultaneously. This is more efficient than reading files one by one when you need to analyze or compare multiple files. Each file's content is returned with its path as a reference. Failed reads for individual files won't stop the entire operation. Only works within allowed directories.
* write_file
  + Create a new file or completely overwrite an existing file with new content. Use with caution as it will overwrite existing files without warning. Handles text content with proper encoding. Only works within allowed directories.
* edit_file
  + Make line-based edits to a text file. Each edit replaces exact line sequences with new content. Returns a git-style diff showing the changes made. Only works within allowed directories.
* create_directory
  + Create a new directory or ensure a directory exists. Can create multiple nested directories in one operation. If the directory already exists, this operation will succeed silently. Perfect for setting up directory structures for projects or ensuring required paths exist. Only works within allowed directories.
* list_directory
  + Get a detailed listing of all files and directories in a specified path. Results clearly distinguish between files and directories with [FILE] and [DIR] prefixes. This tool is essential for understanding directory structure and finding specific files within a directory. Only works within allowed directories.
* list_directory_with_sizes
  + Get a detailed listing of all files and directories in a specified path, including sizes. Results clearly distinguish between files and directories with [FILE] and [DIR] prefixes. This tool is useful for understanding directory structure and finding specific files within a directory. Only works within allowed directories.
* directory_tree
  + Get a recursive tree view of files and directories as a JSON structure. Each entry includes 'name', 'type' (file/directory), and 'children' for directories. Files have no children array, while directories always have a children array (which may be empty). The output is formatted with 2-space indentation for readability. Only works within allowed directories.
* move_file
  + Move or rename files and directories. Can move files between directories and rename them in a single operation. If the destination exists, the operation will fail. Works across different directories and can be used for simple renaming within the same directory. Both source and destination must be within allowed directories.
* search_files
  + Recursively search for files and directories matching a pattern. Searches through all subdirectories from the starting path. The search is case-insensitive and matches partial names. Returns full paths to all matching items. Great for finding files when you don't know their exact location. Only searches within allowed directories.
* get_file_info
  + Retrieve detailed metadata about a file or directory. Returns comprehensive information including size, creation time, last modified time, permissions, and type. This tool is perfect for understanding file characteristics without reading the actual content. Only works within allowed directories.
* list_allowed_directories
  Returns the list of directories that this server is allowed to access. Use this to understand which directories are available before trying to access files.


### MarcusJellinghaus/mcp_server_filesystem

* [MarcusJellinghaus/mcp_server_filesystem](https://github.com/MarcusJellinghaus/mcp_server_filesystem)

### mcp-file-context-server

* [mcp-file-context-server](https://github.com/bsmi021/mcp-file-context-server
  + file operations
  + code analysis
  + smart caching
  + advanced search

## Github

### github-mcp-server

* [github-mcp-server](https://github.com/github/github-mcp-server)
  GitHub's official MCP Server

* extremely long tools list, hence not listed here

### github-action-trigger-mcp - working

* [github-action-trigger-mcp](https://github.com/nextDriveIoE/github-action-trigger-mcp)

* get_github_actions
  + Get available GitHub Actions for a repository
* get_github_action
  + Get detailed information about a specific GitHub Action, including inputs and their requirements
* trigger_github_action
  + Trigger a GitHub workflow dispatch event with custom inputs
* get_github_release
  + Get the latest 2 releases from a GitHub repository

## Memory

### mcp-memory-service - working, based on chroma, container is difficult

* [mcp-memory-service](https://github.com/doobidoo/mcp-memory-service)


* store_memory
  + Store new information with optional tags. Accepts two tag formats in metadata: - Array: ["tag1", "tag2"] - String: "tag1,tag2" 
  + Examples: 
  + # Using array format: 
    { "content": "Memory content", "metadata": { "tags": ["important", "reference"], "type": "note" } }
  + # Using string format(preferred): 
    { "content": "Memory content", "metadata": { "tags": "important,reference", "type": "note" } }
* recall_memory
  + Retrieve memories using natural language time expressions and optional semantic search. Supports various time-related expressions such as: - "yesterday", "last week", "2 days ago" - "last summer", "this month", "last January" - "spring", "winter", "Christmas", "Thanksgiving" - "morning", "evening", "yesterday afternoon" 
  + Examples: 
    { "query": "recall what I stored last week" }
    { "query": "find information about databases from two months ago", "n_results": 5 }
* retrieve_memory
  + Find relevant memories based on query. 
  + Example: { "query": "find this memory", "n_results": 5 }
* search_by_tag
  + Search memories by tags. Must use array format. Returns memories matching ANY of the specified tags.
  + Example: { "tags": ["important", "reference"] }
* delete_memory
  + Delete a specific memory by its hash.
  + Example: { "content_hash": "a1b2c3d4..." }
* delete_by_tag
  + Delete all memories with specific tags. WARNING: Deletes ALL memories containing any of the specified tags. 
  + Example: {"tags": ["temporary", "outdated"]}
* delete_by_tags
  + Delete all memories containing any of the specified tags. This is the explicit multi-tag version for API clarity.
  + WARNING: Deletes ALL memories containing any of the specified tags.
  + Example: { "tags": ["temporary", "outdated", "test"] }
* delete_by_all_tags
  + Delete memories that contain ALL of the specified tags. 
  + WARNING: Only deletes memories that have every one of the specified tags.
  + Example: { "tags": ["important", "urgent"] }
* cleanup_duplicates
  + Find and remove duplicate entries
* get_embedding
  + Get raw embedding vector for content. 
  + Example: { "content": "text to embed" }
* check_embedding_model
  + Check if embedding model is loaded and working
* debug_retrieve
  + Retrieve memories with debug information. 
  + Example: { "query": "debug this", "n_results": 5, "similarity_threshold": 0.0 }
* exact_match_retrieve
  + Retrieve memories using exact content match. 
  + Example: { "content": "find exactly this" }
* check_database_health
  + Check database health and get statistics
* recall_by_timeframe
  + Retrieve memories within a specific timeframe. 
  + Example: { "start_date": "2024-01-01", "end_date": "2024-01-31", "n_results": 5 }
* delete_by_timeframe
  + Delete memories within a specific timeframe. Optional tag parameter to filter deletions. 
  + Example: { "start_date": "2024-01-01", "end_date": "2024-01-31", "tag": "temporary" }
* delete_before_date
  + Delete memories before a specific date. Optional tag parameter to filter deletions.
  + Example: { "before_date": "2024-01-01", "tag": "temporary" }
* dashboard_check_health
  + Dashboard: Retrieve basic database health status, returns JSON.
* dashboard_recall_memory
  + Dashboard: Recall memories by time expressions and return JSON format.
* dashboard_retrieve_memory
  + Dashboard: Retrieve memories and return JSON format.
* dashboard_search_by_tag
  + Dashboard: Search memories by tags and return JSON format.
* dashboard_get_stats
  + Dashboard: Get database statistics and return JSON format.
* dashboard_optimize_db
  + Dashboard: Optimize database and return JSON format.
* dashboard_create_backup
  + Dashboard: Create database backup and return JSON format.
* dashboard_delete_memory
  + Dashboard: Delete a specific memory by ID and return JSON format.

## Podman

### podman-mcp-server -working

* [podman-mcp-server](https://github.com/manusa/podman-mcp-server)


* container_inspect
  + Displays the low-level information and configuration of a Docker or Podman container with the specified container ID or name
* container_list
  + Prints out information about the running Docker or Podman containers
* container_logs
  + Displays the logs of a Docker or Podman container with the specified container ID or name
* container_remove
  + Removes a Docker or Podman container with the specified container ID or name (rm)
* container_run
  + Runs a Docker or Podman container with the specified image name
* container_stop
  + Stops a Docker or Podman running container with the specified container ID or name
* image_build
  + Build a Docker or Podman image from a Dockerfile, Podmanfile, or Containerfile
* image_list
  + List the Docker or Podman images on the local machine
* image_pull
  + Copies (pulls) a Docker or Podman container image from a registry onto the local machine storage
* image_push
  + Pushes a Docker or Podman container image, manifest list or image index from local machine storage to a registry
* image_remove
  + Removes a Docker or Podman image from the local machine storage
* network_list
  + List all the available Docker or Podman networks
* volume_list
  + List all the available Docker or Podman volumes

## shells

## shell-mcp - not recommended

* https://github.com/kevinwatt/shell-mcp
  + only whitelisted commands
  + many errors with claude desktop (because the whitelist seems not be visible to claude?)
  + not recommended
