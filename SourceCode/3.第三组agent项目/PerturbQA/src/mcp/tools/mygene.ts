const MYGENE_API = "https://mygene.info/v3";

export interface GeneAnnotation {
  symbol: string;
  entrezId: string;
  ensemblId: string;
  pathways: { kegg?: string[]; reactome?: string[]; wikipathways?: string[] };
  goTerms: { biological_process?: string[]; molecular_function?: string[]; cellular_component?: string[] };
  omimIds: string[];
  essentialityNote: string;
  summary: string;
}

export async function getGeneAnnotation(geneName: string): Promise<GeneAnnotation | null> {
  const queryUrl = `${MYGENE_API}/query?q=${encodeURIComponent(geneName)}&species=human&fields=symbol,entrezgene,ensembl.gene,pathway,go,omim,summary&size=1`;

  const res = await fetch(queryUrl);
  if (!res.ok) throw new Error(`MyGene.info request failed: ${res.status}`);
  const data = (await res.json()) as any;
  const hit = data?.hits?.[0];
  if (!hit) return null;

  const kegg = hit.pathway?.kegg
    ? (Array.isArray(hit.pathway.kegg) ? hit.pathway.kegg : [hit.pathway.kegg]).map(
        (p: any) => `${p.id}: ${p.name}`
      )
    : [];
  const reactome = hit.pathway?.reactome
    ? (Array.isArray(hit.pathway.reactome) ? hit.pathway.reactome : [hit.pathway.reactome]).map(
        (p: any) => `${p.id}: ${p.name}`
      )
    : [];

  const extractGO = (terms: any[] | any | undefined, field: string): string[] => {
    if (!terms) return [];
    const arr = Array.isArray(terms) ? terms : [terms];
    return arr.slice(0, 5).map((t: any) => `${t.id}: ${t.term}`);
  };

  const omimIds = hit.omim
    ? Array.isArray(hit.omim)
      ? hit.omim.map(String)
      : [String(hit.omim)]
    : [];

  return {
    symbol: hit.symbol ?? geneName,
    entrezId: hit.entrezgene ? String(hit.entrezgene) : "",
    ensemblId: hit.ensembl?.gene ?? "",
    pathways: { kegg, reactome },
    goTerms: {
      biological_process: extractGO(hit.go?.BP, "BP"),
      molecular_function: extractGO(hit.go?.MF, "MF"),
      cellular_component: extractGO(hit.go?.CC, "CC"),
    },
    omimIds,
    essentialityNote:
      omimIds.length > 0
        ? `Associated with ${omimIds.length} OMIM disease entries, suggesting functional importance.`
        : "No OMIM disease associations found.",
    summary: hit.summary ?? "No summary available.",
  };
}

export const MYGENE_TOOL = {
  name: "get_gene_annotation",
  description:
    "Query MyGene.info for comprehensive gene annotation including pathway membership (KEGG, Reactome), Gene Ontology terms, and disease associations. Useful for understanding the biological context of gene perturbation targets and predicting downstream effects.",
  inputSchema: {
    type: "object",
    properties: {
      gene_name: {
        type: "string",
        description: "Gene symbol (e.g., 'TP53', 'KRAS', 'EGFR')",
      },
    },
    required: ["gene_name"],
  },
};
