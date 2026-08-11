import "server-only";
import Anthropic from "@anthropic-ai/sdk";
import type { MessageParam, ToolResultBlockParam } from "@anthropic-ai/sdk/resources/messages";
import { connectMcpClient, listMcpToolsForAnthropic, callMcpTool } from "@/lib/mcpClient";

export const runtime = "nodejs";

const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });
const MODEL = "claude-sonnet-5";
const MAX_TOOL_ROUNDS = 6;

type ChatMessage = { role: "user" | "assistant"; content: string };

export async function POST(req: Request) {
  const { messages } = (await req.json()) as { messages: ChatMessage[] };

  if (!Array.isArray(messages) || messages.length === 0) {
    return Response.json({ error: "messages is required" }, { status: 400 });
  }

  const mcp = await connectMcpClient();
  const toolCallLog: { tool: string; input: unknown }[] = [];

  try {
    const tools = await listMcpToolsForAnthropic(mcp);

    const conversation: MessageParam[] = messages.map((m) => ({
      role: m.role,
      content: m.content,
    }));

    let response = await anthropic.messages.create({
      model: MODEL,
      max_tokens: 1024,
      tools,
      messages: conversation,
    });

    let rounds = 0;
    while (response.stop_reason === "tool_use" && rounds < MAX_TOOL_ROUNDS) {
      rounds += 1;
      conversation.push({ role: "assistant", content: response.content });

      const toolResults: ToolResultBlockParam[] = [];
      for (const block of response.content) {
        if (block.type !== "tool_use") continue;

        toolCallLog.push({ tool: block.name, input: block.input });
        const result = await callMcpTool(
          mcp,
          block.name,
          block.input as Record<string, unknown>
        );

        toolResults.push({
          type: "tool_result",
          tool_use_id: block.id,
          content: JSON.stringify(result.content),
        });
      }

      conversation.push({ role: "user", content: toolResults });

      response = await anthropic.messages.create({
        model: MODEL,
        max_tokens: 1024,
        tools,
        messages: conversation,
      });
    }

    const reply = response.content
      .filter((block) => block.type === "text")
      .map((block) => block.text)
      .join("\n");

    console.log("[agent] tool calls:", JSON.stringify(toolCallLog));

    return Response.json({ reply, toolCalls: toolCallLog });
  } finally {
    await mcp.close();
  }
}
