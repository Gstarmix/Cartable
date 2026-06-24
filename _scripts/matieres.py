from __future__ import annotations
from dataclasses import dataclass
EMOJI_SEM = {"S1": "📕", "S2": "📗"}
@dataclass(frozen=True)
class Matiere:
    semestre: str
    libelle: str
    slug: str
    has_td: bool
    @property
    def categorie_discord(self) -> str:
        return f"{EMOJI_SEM[self.semestre]} {self.semestre} · {self.libelle}"
MATIERES: list[Matiere] = [
    Matiere("S1", "Droit des personnes", "droit-personnes", True),
    Matiere("S1", "Droit constitutionnel 1", "constit1", True),
    Matiere("S1", "Histoire des institutions publiques", "hist-inst", True),
    Matiere("S1", "Introduction au droit & juridictions", "intro-droit", False),
    Matiere("S1", "Organisations européennes", "orga-europ", False),
    Matiere("S2", "Droit de la famille", "droit-famille", True),
    Matiere("S2", "Droit constitutionnel 2", "constit2", True),
    Matiere("S2", "Histoire des sources du droit", "hist-sources", False),
    Matiere("S2", "Institutions administratives", "inst-admin", False),
    Matiere("S2", "Histoire du droit des personnes et de la famille", "hist-droit-perso", False),
    Matiere("S2", "Relations internationales", "relations-inter", False),
    Matiere("S2", "Introduction à la science politique", "science-po", False),
    Matiere("S2", "Anglais", "anglais", False),
]
BY_SLUG: dict[str, Matiere] = {m.slug: m for m in MATIERES}
def get(slug: str) -> Matiere | None:
    return BY_SLUG.get(slug.lower())
def slugs(semestre: str | None = None) -> list[str]:
    return [m.slug for m in MATIERES if semestre is None or m.semestre == semestre]
if __name__ == "__main__":
    for m in MATIERES:
        td = "CM+TD" if m.has_td else "CM   "
        print(f"  {m.semestre}  {td}  {m.slug:18}  {m.categorie_discord}")