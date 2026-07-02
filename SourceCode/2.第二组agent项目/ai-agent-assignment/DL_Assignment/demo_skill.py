from src.skills.pubchem_skill import PubChemSkill
import json
skill = PubChemSkill()
print(json.dumps(skill.get_compound_properties("aspirin"), indent=2))
