// Uses MyGene.info API (aggregates NCBI Gene + UniProt + Ensembl data)
const MYGENE_API = "https://mygene.info/v3";

export interface GeneInfo {
  id: string;
  name: string;
  fullName: string;
  aliases: string[];
  summary: string;
  chromosome: string;
  organism: string;
  geneType: string;
  entrezId: string;
  ensemblId: string;
}

export async function searchGeneInfo(
  geneName: string,
  organism: string = "human"
): Promise<GeneInfo | null> {
  const url = `${MYGENE_API}/query?q=${encodeURIComponent(geneName)}&species=${encodeURIComponent(organism)}&fields=symbol,name,other_names,summary,genomic_pos,type_of_gene,entrezgene,ensembl.gene,taxid&size=1`;

  const res = await fetch(url);
  if (!res.ok) throw new Error(`MyGene.info request failed: ${res.status}`);
  const data = (await res.json()) as any;
  const hit = data?.hits?.[0];
  if (!hit) return null;

  const aliases = hit.other_names
    ? Array.isArray(hit.other_names)
      ? hit.other_names
      : [hit.other_names]
    : [];

  const pos = hit.genomic_pos;
  const chromosome = pos
    ? Array.isArray(pos)
      ? pos[0]?.chr ?? "unknown"
      : pos.chr ?? "unknown"
    : "unknown";

  return {
    id: hit._id ?? "",
    name: hit.symbol ?? geneName,
    fullName: hit.name ?? "",
    aliases,
    summary: hit.summary ?? "No summary available.",
    chromosome: String(chromosome),
    organism,
    geneType: hit.type_of_gene ?? "unknown",
    entrezId: hit.entrezgene ? String(hit.entrezgene) : "",
    ensemblId: hit.ensembl?.gene ?? "",
  };
}

export const NCBI_GENE_TOOL = {
  name: "search_gene_info",
  description:
    "Search for detailed gene information (gene symbol, full name, aliases, chromosomal location, biological summary) using the MyGene.info API which aggregates NCBI Gene, Ensembl, and UniProt data. Useful for identifying gene function and perturbation targets.",
  inputSchema: {
    type: "object",
    properties: {
      gene_name: {
        type: "string",
        description: "Gene symbol or name (e.g., 'TP53', 'BRCA1', 'KRAS')",
      },
      organism: {
        type: "string",
        description: "Organism name (default: 'human')",
        default: "human",
      },
    },
    required: ["gene_name"],
  },
};
