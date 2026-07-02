import requests
from pathlib import Path
from urllib.parse import quote
from ..utils import append_jsonl, now_iso

class PubChemSkill:
    """MCP/SKILL-style PubChem integration.

    Exposes three interfaces: search_compound, get_compound_properties, get_synonyms.
    """
    BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

    def __init__(self, log_path="logs/skill_invocations.jsonl", timeout=8):
        self.log_path = Path(log_path)
        self.timeout = timeout

    def _log(self, tool_name, args, result, ok=True):
        append_jsonl(self.log_path, {"time": now_iso(), "skill":"pubchem", "tool_name": tool_name, "args": args, "ok": ok, "result_preview": str(result)[:500]})

    def get_compound_properties(self, name):
        # PubChem PUG-REST may return different SMILES labels across endpoints/releases.
        # Request the common fields and normalize them so the UI never prints "None".
        props = "MolecularFormula,MolecularWeight,CanonicalSMILES,IsomericSMILES,IUPACName,InChIKey"
        safe_name = quote(str(name).strip())
        url = f"{self.BASE}/compound/name/{safe_name}/property/{props}/JSON"
        try:
            r = requests.get(url, timeout=self.timeout)
            r.raise_for_status()
            data = r.json()["PropertyTable"]["Properties"][0]
            # Compatibility aliases for systems that use alternative PubChem/cheminformatics names.
            if not data.get("CanonicalSMILES"):
                data["CanonicalSMILES"] = data.get("ConnectivitySMILES") or data.get("SMILES") or data.get("IsomericSMILES")
            self._log("get_compound_properties", {"name": name}, data, True)
            return {"ok": True, "compound": name, "properties": data}
        except Exception as e:
            result = {"ok": False, "compound": name, "error": str(e), "recovery": "Use internal knowledge retrieval or ask for another compound name."}
            self._log("get_compound_properties", {"name": name}, result, False)
            return result

    def search_compound(self, name):
        url = f"{self.BASE}/compound/name/{name}/cids/JSON"
        try:
            r = requests.get(url, timeout=self.timeout)
            r.raise_for_status()
            cids = r.json().get("IdentifierList", {}).get("CID", [])
            result = {"ok": True, "compound": name, "cids": cids[:10]}
            self._log("search_compound", {"name": name}, result, True)
            return result
        except Exception as e:
            result = {"ok": False, "compound": name, "error": str(e)}
            self._log("search_compound", {"name": name}, result, False)
            return result

    def get_synonyms(self, name):
        url = f"{self.BASE}/compound/name/{name}/synonyms/JSON"
        try:
            r = requests.get(url, timeout=self.timeout)
            r.raise_for_status()
            syns = r.json().get("InformationList", {}).get("Information", [{}])[0].get("Synonym", [])
            result = {"ok": True, "compound": name, "synonyms": syns[:20]}
            self._log("get_synonyms", {"name": name}, result, True)
            return result
        except Exception as e:
            result = {"ok": False, "compound": name, "error": str(e)}
            self._log("get_synonyms", {"name": name}, result, False)
            return result
