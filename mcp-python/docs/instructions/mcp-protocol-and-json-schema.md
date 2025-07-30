<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" class="logo" width="120"/>

# On a MCP server, regarding tool endpoints: How are the arguments to the tool endpoint defined? How is the result/respose of an tool endpoint defined? Are there strict rules?

On an MCP (Model Context Protocol) server, **tool endpoints**—the functions that large language models or clients can call—are defined with explicit schemas and follow a set of conventions and requirements as laid out by the MCP specification.

### Arguments to Tool Endpoints

- **Arguments are defined via a "parameter schema" or "input schema"**. This schema is typically described using a JSON-compatible structure, and it specifies:
    - The **names** of arguments.
    - The **types** (e.g., string, int, boolean, etc.).
    - Whether parameters are **required or optional**.
    - Optionally, parameter descriptions and validation constraints.

Example:

```json
"parameters": {
  "host": {"type": "string", "required": true, "description": "API host"},
  "sort": {"type": "string", "required": false, "description": "Sort order"}
}
```

- The tool manifest (a machine-readable manifest that exposes all available tools) describes these schemas for each tool the server exposes[^1_1][^1_2][^1_3].
- When a client calls a tool endpoint, it sends the arguments as a JSON object matching this schema.


### Tool Endpoint Response/Result

- **Results are also strictly defined:** each tool must define an **output schema** (sometimes "results schema"), typically described in JSON schema format or as part of the tool manifest.
- The **result** returned is a JSON object that matches this output schema.
- If there’s an error, the response must conform to the standard **JSON-RPC error format** (error code, message, optional data), as specified by the protocol[^1_2][^1_3][^1_4].

Example "success" response:

```json
{
  "jsonrpc": "2.0",
  "id": "<request id>",
  "result": {"items": [...], "total": 123}
}
```

Example "error" response:

```json
{
  "jsonrpc": "2.0",
  "id": "<request id>",
  "error": {
    "code": -32000,
    "message": "Invalid input parameters"
  }
}
```


### Are There Strict Rules?

- **Yes**—there are strict rules:
    - Tool arguments and results must conform to the declared schemas in the tool manifest.
    - All tool call requests and responses are handled using the **JSON-RPC 2.0 protocol** for message format and correlation[^1_4].
    - Errors and exceptions must be reported in standard structures.
- This strictness enables client applications (including LLMs) to **discover, call, and validate** tools automatically, and to handle responses and errors reliably[^1_2][^1_3][^1_1][^1_4].


### Summary Table

| Aspect | How It’s Defined | Standardization? |
| :-- | :-- | :-- |
| Tool arguments | Input/parameter schema (JSON-compatible) | Required |
| Tool result/response | Output/result schema (JSON-compatible) | Required |
| Error handling | JSON-RPC 2.0 error format | Strictly required |
| Message format | JSON-RPC 2.0 request/response | Strictly required |
| Discovery/documentation | Manifest lists tool names, descriptions, schemas | Strictly required |

This schema- and protocol-based approach allows robust, secure, and model-agnostic access to external tools via MCP servers[^1_1][^1_2][^1_3][^1_4].

<div style="text-align: center">⁂</div>

[^1_1]: https://simplescraper.io/blog/how-to-mcp

[^1_2]: https://www.speakeasy.com/mcp/building-servers/protocol-reference/tools

[^1_3]: https://vercel.com/blog/model-context-protocol-mcp-explained

[^1_4]: https://blog.christianposta.com/understanding-mcp-authorization-step-by-step/

[^1_5]: https://modelcontextprotocol.io/specification/2025-06-18/server/tools

[^1_6]: https://cookbook.openai.com/examples/mcp/mcp_tool_guide

[^1_7]: https://learn.microsoft.com/en-us/azure/azure-functions/functions-bindings-mcp-trigger

[^1_8]: https://forum.cursor.com/t/cursor-cannot-handle-mcp-server-params/52657

[^1_9]: https://www.philschmid.de/mcp-introduction

[^1_10]: https://modelcontextprotocol.io/specification/2025-03-26/basic/transports

[^1_11]: https://learn.microsoft.com/en-us/azure/developer/azure-mcp-server/tools/

[^1_12]: https://docs.meingpt.com/en/developer/mcp-tooling

[^1_13]: https://docs.cursor.com/context/model-context-protocol

[^1_14]: https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/tools/model-context-protocol

[^1_15]: https://docs.anthropic.com/en/docs/mcp

[^1_16]: https://www.reddit.com/r/mcp/comments/1jr8if3/i_cant_understand_the_hype/

[^1_17]: https://modelcontextprotocol.io/quickstart/server

[^1_18]: https://community.openai.com/t/this-mcp-server-violates-our-guidelines/1279211


---

# So there is JSON schema for the result, but _not_ for the arguments, right?

There is a JSON schema for both the **arguments (input parameters) and the result (output)** of a tool endpoint on an MCP server.

- The **arguments** to a tool endpoint are defined using a parameter or input schema, typically using a JSON-compatible schema, and this is required when registering or describing the tool to the MCP server[^2_2][^2_1][^2_4]. For example, tools are registered with schemas such as:

```js
schema: z.object({
  a: z.number(),
  b: z.number()
})
```

- The **result/response** of the tool is also defined using a JSON schema or output schema, and the tool must return data that matches this format[^2_1][^2_2].

So, to clarify: MCP requires **both argument and result JSON schemas** for tool endpoints, and both are strictly enforced as part of the tool definition and manifest[^2_1][^2_2][^2_4].

<div style="text-align: center">⁂</div>

[^2_1]: https://langchain-ai.github.io/langgraph/concepts/server-mcp/

[^2_2]: https://simplescraper.io/blog/how-to-mcp

[^2_3]: https://zuplo.com/docs/handlers/mcp-server

[^2_4]: https://zuplo.com/docs/handlers/mcp-server-custom-tools

[^2_5]: https://modelcontextprotocol.io/specification/2025-06-18/server/tools

[^2_6]: https://cookbook.openai.com/examples/mcp/mcp_tool_guide

[^2_7]: https://docs.anthropic.com/en/docs/claude-code/mcp

[^2_8]: https://community.openai.com/t/mcp-client-sse-cant-use-tools-in-mcp-server-sse/1262420

[^2_9]: https://www.reddit.com/r/mcp/comments/1kezfpm/why_does_mcp_lack_response_schema/


---

# Is this the same for prompt endpoints? And if yes, for what are resources endpoint needed?

**Prompt endpoints** in MCP also utilize schemas, but their function and requirements differ from those of tool endpoints:

- For **prompt endpoints**, the schemas primarily define *pre-built prompt templates* or prompt objects that the host application or user can select and supply to the LLM during inference[^3_1][^3_3].
- These endpoints expose strings and meta-information (such as titles, descriptions, and sometimes parameterizable slots), not functions that take arbitrary arguments and produce structured output.
- Accordingly, prompt endpoints do not define *input/output schemas* for arbitrary arguments and results in the way tool endpoints do. Instead, their schema covers the prompt's metadata and optional variable slots (e.g., placeholders for personalized or context-sensitive data)[^3_1][^3_3].

**Why are resources endpoints needed?**

- **Resource endpoints** serve a different purpose: they expose *external data sources* as context that can be injected into the LLM session[^3_1][^3_3].
- These are analogous to RESTful GET endpoints, providing structured data (databases, records, files, etc.) for the model to "read" and reference, but without performing actions or side effects.
- This separation exists because *resources* are designed for bulk data/context (reference), while *tools* are for actions, and *prompts* are static templates.

**Summary Table**


| Endpoint Type | Schema for Arguments/Results | Purpose |
| :-- | :-- | :-- |
| Tools | Yes (JSON schema for both) | Execute actions with parameters, return results |
| Resources | Yes (JSON schema for output) | Expose data for models to reference |
| Prompts | Yes (for metadata \& slots only) | Provide reusable prompt texts/templates |

**Key distinctions:**

- **Prompts**: Schema covers template and metadata, not arbitrary input/output.
- **Resources**: Schema covers data structure, not actions; provides context.
- **Tools**: Strict schema for arguments and result, because it's for function invocation.

This separation of concerns in MCP enables safe, predictable integration points for action (tools), data (resources), and user-controlled prompts[^3_1][^3_3].

<div style="text-align: center">⁂</div>

[^3_1]: https://www.philschmid.de/mcp-introduction

[^3_2]: https://simplescraper.io/blog/how-to-mcp

[^3_3]: https://stytch.com/blog/model-context-protocol-introduction/

[^3_4]: https://modelcontextprotocol.io

[^3_5]: https://modelcontextprotocol.io/specification/2025-06-18/server/tools

[^3_6]: https://docs.anthropic.com/en/docs/mcp

[^3_7]: https://vercel.com/blog/model-context-protocol-mcp-explained

[^3_8]: https://github.com/modelcontextprotocol/python-sdk

[^3_9]: https://docs.cursor.com/context/mcp


---

# Can resources be descripted with JSON schema as well? How? Give a simple example for prompt with arguments slot (and schema for arguments and result, if applicable).

Yes, **resources can be described with JSON Schema** in MCP, in the same way as tool endpoints—but primarily for their *output/data structure*, since resources are typically "read-only" or provide contextual data to the model.

- The **resource's output format** (e.g., the structure of the returned data) is defined by a JSON Schema, so clients and LLMs know exactly what fields and types to expect[^4_8].
- This schema is usually provided in the MCP resource or template manifest[^4_2][^4_8].
- Resources generally do not take complex arguments like tools but may accept simple parameters such as query strings or cursors for pagination.

**Example: Resource with JSON Schema Output**

```json
{
  "name": "userProfiles",
  "description": "List of user profiles",
  "schema": {
    "type": "object",
    "properties": {
      "users": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "userId": { "type": "string" },
            "displayName": { "type": "string" }
          },
          "required": ["userId", "displayName"]
        }
      },
      "nextCursor": { "type": "string" }
    },
    "required": ["users"]
  }
}
```

This allows the LLM or client to interpret and use the resource's data predictably[^4_8].

**Prompt Endpoints: Example with Argument Slot**

- **Prompt endpoints** may define *slots* (arguments) that users or clients can supply. Each slot can have its own JSON Schema describing the expected type.
- There is typically **no result schema**, since the primary result is always a prompt string (possibly formatted/finalized with the arguments).

**Example: Prompt Template with Arguments**

```json
{
  "name": "greetingPrompt",
  "description": "A prompt to greet a user by name.",
  "template": "Hello, {{userName}}! Welcome.",
  "slots": {
    "userName": {
      "type": "string",
      "description": "The name of the user to greet."
    }
  }
}
```

- Here, the slot **userName** is described with a JSON-compatible schema (type "string").
- When called, you supply `{ "userName": "Alice" }` as the arguments, and receive `"Hello, Alice! Welcome."` as the rendered prompt.
- Most prompt endpoints do *not* declare a result schema, as the output is always a filled-in prompt string.

**Summary Table**


| Endpoint Type | Arguments Schema | Result Schema | Example |
| :-- | :-- | :-- | :-- |
| Resource | Often minimal/simple | Yes (JSON Schema) | See above |
| Prompt | Yes (for slots) | No* | See above |

(*Prompt result is always a text string; not a structured JSON object.)

**In essence:** Both resources and prompt slot arguments can and should be described with JSON Schema for clarity and reliability in MCP-based integrations[^4_8][^4_2].

<div style="text-align: center">⁂</div>

[^4_1]: https://treblle.com/blog/model-context-protocol-guide

[^4_2]: https://github.com/modelcontextprotocol/specification/blob/main/schema/2024-11-05/schema.json

[^4_3]: https://www.stainless.com/mcp/mcp-api-documentation-the-complete-guide

[^4_4]: https://github.com/modelcontextprotocol/modelcontextprotocol

[^4_5]: https://docs.anthropic.com/en/docs/claude-code/mcp

[^4_6]: https://www.seangoedecke.com/model-context-protocol/

[^4_7]: https://customgpt.ai/mcp-features/

[^4_8]: https://www.philschmid.de/mcp-introduction

[^4_9]: https://www.getambassador.io/blog/model-context-protocol-mcp-connecting-llms-to-apis


---

# Is it recommended to use JSON schema in all 3 cases?

Yes, it is **strongly recommended to use JSON Schema in all three cases**—tools, resources, and prompts—in MCP servers for the following reasons:

- **Tools:** JSON Schema is essential and strictly required to define both the input arguments and output results. This strict schema enforcement ensures correct and predictable invocation and response handling, necessary for client validation and error checking[^5_1][^5_3].
- **Resources:** JSON Schema is used primarily to describe the structure of the data returned by resource endpoints. Since resources provide contextual data for the model to reference, having a JSON Schema ensures clients and LLMs understand the exact data shape, field types, and constraints[^5_1][^5_3].
- **Prompts:** While prompt endpoints do not have structured input/output like tools, the argument *slots* (placeholders) within prompts should be described using JSON Schema or JSON-compatible descriptors. This allows clients to validate and supply correct values, improving reliability and predictability in prompt construction[^5_1].

In summary, JSON Schema serves as the lingua franca for defining data structure and validation consistently across MCP endpoint types, helping to avoid errors and increase interoperability. Best practices in MCP server development consistently endorse using JSON Schema for inputs, outputs, and argument slots wherever applicable[^5_1][^5_3][^5_7].

If you are building or designing MCP servers, leveraging JSON Schema for all three endpoint types is therefore recommended as a best practice to ensure robust, clear, and validated API interactions.

Citations:

- [^5_1] Debugging Model Context Protocol (MCP) Servers: Tips and Best Practices (2025)
- [^5_3] Best Practices for MCP Servers - LinkedIn (2025)
- [^5_7] How to Build an MCP Server: Setup and Management Guide (2025)

<div style="text-align: center">⁂</div>

[^5_1]: https://www.mcpevals.io/blog/debugging-mcp-servers-tips-and-best-practices

[^5_2]: https://dev.to/samchon/why-your-mcp-server-fails-how-to-make-100-successful-mcp-server-iem

[^5_3]: https://www.linkedin.com/pulse/best-practices-mcp-servers-gaurang-desai-7ptqc

[^5_4]: https://www.merge.dev/blog/mcp-best-practices

[^5_5]: https://engineering.block.xyz/blog/blocks-playbook-for-designing-mcp-servers

[^5_6]: https://www.infracloud.io/blogs/build-your-own-mcp-server/

[^5_7]: https://blog.promptlayer.com/how-to-build-mcp-server/

[^5_8]: https://www.flowhunt.io/blog/mcp-server-development-guide/

