import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

import { searchGeneInfo, NCBI_GENE_TOOL } from "./tools/ncbi-gene.js";
import { getProteinInteractions, STRING_DB_TOOL } from "./tools/string-db.js";
import { getGeneAnnotation, MYGENE_TOOL } from "./tools/mygene.js";

const server = new Server(
  { name: "perturbqa-gene-tools", version: "0.1.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [NCBI_GENE_TOOL, STRING_DB_TOOL, MYGENE_TOOL],
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  const toolArgs = (args ?? {}) as Record<string, unknown>;

  try {
    if (name === "search_gene_info") {
      const result = await searchGeneInfo(toolArgs.gene_name as string, toolArgs.organism as string | undefined);
      if (!result) {
        return { content: [{ type: "text", text: `Gene '${toolArgs.gene_name}' not found in NCBI Gene.` }] };
      }
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(result, null, 2),
          },
        ],
      };
    }

    if (name === "get_protein_interactions") {
      const result = await getProteinInteractions(
        toolArgs.gene_name as string,
        9606,
        (toolArgs.limit as number | undefined) ?? 10,
        (toolArgs.min_score as number | undefined) ?? 400
      );
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    }

    if (name === "get_gene_annotation") {
      const result = await getGeneAnnotation(toolArgs.gene_name as string);
      if (!result) {
        return { content: [{ type: "text", text: `No annotation found for '${toolArgs.gene_name}'.` }] };
      }
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    }

    throw new Error(`Unknown tool: ${name}`);
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    return { content: [{ type: "text", text: `Error: ${msg}` }], isError: true };
  }
});

const transport = new StdioServerTransport();
await server.connect(transport);
console.error("PerturbQA MCP server running on stdio");
