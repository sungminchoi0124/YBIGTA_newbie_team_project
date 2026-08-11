import "server-only";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { SSEClientTransport } from "@modelcontextprotocol/sdk/client/sse.js";

const MCP_SERVER_URL = process.env.MCP_SERVER_URL;
const MCP_AUTH_TOKEN = process.env.MCP_AUTH_TOKEN;

export async function connectMcpClient(): Promise<Client> {
  if (!MCP_SERVER_URL) {
    throw new Error("MCP_SERVER_URL is not set");
  }

  const client = new Client({ name: "ybigta-data-agent", version: "1.0.0" });
  const transport = new SSEClientTransport(new URL(MCP_SERVER_URL), {
    fetch: (input, init) => {
      const headers = new Headers(init?.headers);
      if (MCP_AUTH_TOKEN) headers.set("Authorization", `Bearer ${MCP_AUTH_TOKEN}`);
      return fetch(input, { ...init, headers });
    },
  });

  await client.connect(transport);
  return client;
}

export async function listMcpToolsForAnthropic(client: Client) {
  const { tools } = await client.listTools();
  return tools.map((tool) => ({
    name: tool.name,
    description: tool.description ?? "",
    input_schema: tool.inputSchema,
  }));
}

export async function callMcpTool(
  client: Client,
  name: string,
  args: Record<string, unknown>
) {
  return client.callTool({ name, arguments: args });
}
