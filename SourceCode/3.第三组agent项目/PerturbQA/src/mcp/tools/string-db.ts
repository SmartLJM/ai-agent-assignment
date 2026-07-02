const STRING_API = "https://string-db.org/api/json";

export interface ProteinInteraction {
  partner: string;
  partnerFullName: string;
  score: number;
  experimentScore: number;
  coexpressionScore: number;
  databaseScore: number;
  textminingScore: number;
}

export interface InteractionResult {
  gene: string;
  organism: string;
  interactions: ProteinInteraction[];
}

export async function getProteinInteractions(
  geneName: string,
  speciesTaxId: number = 9606,
  limit: number = 10,
  minScore: number = 400
): Promise<InteractionResult> {
  const url =
    `${STRING_API}/interaction_partners?identifiers=${encodeURIComponent(geneName)}&species=${speciesTaxId}&limit=${limit}&required_score=${minScore}`;

  const res = await fetch(url);
  if (!res.ok) throw new Error(`STRING DB request failed: ${res.status}`);

  const data = (await res.json()) as any[];
  const interactions: ProteinInteraction[] = data.map((item: any) => ({
    partner: item.preferredName_B ?? item.stringId_B,
    partnerFullName: item.annotation ?? "",
    score: Math.round((item.score ?? 0) * 1000) / 1000,
    experimentScore: Math.round((item.escore ?? 0) * 1000) / 1000,
    coexpressionScore: Math.round((item.coexpression ?? 0) * 1000) / 1000,
    databaseScore: Math.round((item.database ?? 0) * 1000) / 1000,
    textminingScore: Math.round((item.textmining ?? 0) * 1000) / 1000,
  }));

  return { gene: geneName, organism: `taxid:${speciesTaxId}`, interactions };
}

export const STRING_DB_TOOL = {
  name: "get_protein_interactions",
  description:
    "Query STRING database for protein-protein interaction partners of a gene. Returns interaction partners with confidence scores broken down by evidence type (experimental, coexpression, database, text-mining). Useful for understanding gene perturbation effects in interaction networks.",
  inputSchema: {
    type: "object",
    properties: {
      gene_name: {
        type: "string",
        description: "Gene/protein symbol (e.g., 'TP53', 'EGFR')",
      },
      limit: {
        type: "number",
        description: "Maximum number of interaction partners to return (default: 10)",
        default: 10,
      },
      min_score: {
        type: "number",
        description: "Minimum interaction confidence score 0-1000 (default: 400 = medium confidence)",
        default: 400,
      },
    },
    required: ["gene_name"],
  },
};
