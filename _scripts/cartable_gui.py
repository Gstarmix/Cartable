from __future__ import annotations
import os
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "_scripts"
DROIT = ROOT / "DROIT"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import matieres
AUDIO_TYPES = [
    ("Audio", "*.m4a *.mp3 *.wav *.ogg *.flac *.aac *.opus *.mp4 *.webm"),
    ("Tous les fichiers", "*.*"),
]
def _transcription_dir(mat: matieres.Matiere, typ: str) -> Path:
    return DROIT / mat.slug / ("CM/transcriptions" if typ == "CM" else "TD")
def _fiche_dir(mat: matieres.Matiere, typ: str) -> Path:
    return DROIT / mat.slug / ("CM/fiches" if typ == "CM" else "TD")
def canonical_stem(typ: str, num: str, slug: str, date: str) -> str:
    return f"{typ}{num}_{slug}_{date}"
def find_latest_transcription(mat: matieres.Matiere, typ: str, num: str) -> Path | None:
    folder = _transcription_dir(mat, typ)
    if not folder.is_dir():
        return None
    cands = sorted(folder.glob(f"{typ}{num}_{mat.slug}_*.txt"), reverse=True)
    return cands[0] if cands else None
class CartableGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.title("Cartable : production de contenu")
        root.minsize(720, 560)
        self._mats = matieres.MATIERES
        self._label_to_mat = {
            f"{m.semestre} · {m.libelle}": m for m in self._mats
        }
        self.matiere_label = tk.StringVar()
        self.type_code = tk.StringVar(value="CM")
        self.num = tk.StringVar(value="1")
        self.date = tk.StringVar(value=datetime.now().strftime("%d%m"))
        self.audio_path = tk.StringVar()
        self.do_transcribe = tk.BooleanVar(value=True)
        self.do_fiche = tk.BooleanVar(value=True)
        self.do_pub_trans = tk.BooleanVar(value=False)
        self.do_pub_fiche = tk.BooleanVar(value=False)
        self.force_fiche = tk.BooleanVar(value=False)
        self.dry_run = tk.BooleanVar(value=False)
        self._running = False
        self._build_ui()
        if self._mats:
            first = f"{self._mats[0].semestre} · {self._mats[0].libelle}"
            self.matiere_label.set(first)
            self._on_matiere_change()
    def _build_ui(self) -> None:
        pad = dict(padx=6, pady=4)
        top = ttk.Frame(self.root)
        top.pack(fill="x", **pad)
        top.grid_columnconfigure(1, weight=1)
        ttk.Label(top, text="Matière").grid(row=0, column=0, sticky="w")
        self.matiere_combo = ttk.Combobox(
            top, textvariable=self.matiere_label, state="readonly",
            values=list(self._label_to_mat.keys()), width=42,
        )
        self.matiere_combo.grid(row=0, column=1, columnspan=3, sticky="ew", padx=4)
        self.matiere_combo.bind(
            "<<ComboboxSelected>>", lambda e: self._on_matiere_change()
        )
        ttk.Label(top, text="Type").grid(row=1, column=0, sticky="w", pady=(6, 0))
        tframe = ttk.Frame(top)
        tframe.grid(row=1, column=1, sticky="w", pady=(6, 0))
        self.rb_cm = ttk.Radiobutton(tframe, text="CM", value="CM",
                                     variable=self.type_code,
                                     command=self._refresh_targets)
        self.rb_cm.pack(side="left")
        self.rb_td = ttk.Radiobutton(tframe, text="TD", value="TD",
                                     variable=self.type_code,
                                     command=self._refresh_targets)
        self.rb_td.pack(side="left", padx=(10, 0))
        ttk.Label(top, text="N°").grid(row=1, column=2, sticky="e", pady=(6, 0))
        num_e = ttk.Entry(top, textvariable=self.num, width=6)
        num_e.grid(row=1, column=3, sticky="w", padx=4, pady=(6, 0))
        self.num.trace_add("write", lambda *_: self._refresh_targets())
        ttk.Label(top, text="Date (JJMM)").grid(row=2, column=0, sticky="w", pady=(6, 0))
        date_e = ttk.Entry(top, textvariable=self.date, width=8)
        date_e.grid(row=2, column=1, sticky="w", padx=4, pady=(6, 0))
        self.date.trace_add("write", lambda *_: self._refresh_targets())
        ttk.Label(top, text="Fichier audio").grid(row=3, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(top, textvariable=self.audio_path).grid(
            row=3, column=1, columnspan=2, sticky="ew", padx=4, pady=(6, 0)
        )
        ttk.Button(top, text="Parcourir…", command=self._browse_audio).grid(
            row=3, column=3, sticky="e", pady=(6, 0)
        )
        steps = ttk.LabelFrame(self.root, text="Étapes à exécuter")
        steps.pack(fill="x", **pad)
        ttk.Checkbutton(steps, text="① Transcrire l'audio",
                        variable=self.do_transcribe,
                        command=self._refresh_targets).grid(row=0, column=0, sticky="w", padx=8, pady=2)
        ttk.Checkbutton(steps, text="② Générer la fiche de révision",
                        variable=self.do_fiche,
                        command=self._refresh_targets).grid(row=1, column=0, sticky="w", padx=8, pady=2)
        ttk.Checkbutton(steps, text="③ Publier la transcription sur Discord",
                        variable=self.do_pub_trans).grid(row=2, column=0, sticky="w", padx=8, pady=2)
        ttk.Checkbutton(steps, text="④ Publier la fiche sur Discord",
                        variable=self.do_pub_fiche).grid(row=3, column=0, sticky="w", padx=8, pady=2)
        ttk.Checkbutton(steps, text="Régénérer la fiche si elle existe déjà (--force)",
                        variable=self.force_fiche).grid(row=0, column=1, sticky="w", padx=8, pady=2)
        ttk.Checkbutton(steps, text="Simulation (dry-run, n'écrit/ne poste rien)",
                        variable=self.dry_run).grid(row=1, column=1, sticky="w", padx=8, pady=2)
        self.targets_var = tk.StringVar()
        ttk.Label(self.root, textvariable=self.targets_var, foreground="#555",
                  justify="left").pack(fill="x", padx=8)
        btns = ttk.Frame(self.root)
        btns.pack(fill="x", **pad)
        self.btn_run = ttk.Button(btns, text="▶ Lancer", command=self._on_run)
        self.btn_run.pack(side="left")
        ttk.Button(btns, text="Effacer le journal",
                   command=self._clear_log).pack(side="left", padx=8)
        logf = ttk.LabelFrame(self.root, text="Journal")
        logf.pack(fill="both", expand=True, **pad)
        self.log = tk.Text(logf, height=14, wrap="word", state="disabled",
                           font=("Consolas", 9))
        scroll = ttk.Scrollbar(logf, command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.log.pack(side="left", fill="both", expand=True)
    def _current_mat(self) -> matieres.Matiere | None:
        return self._label_to_mat.get(self.matiere_label.get())
    def _on_matiere_change(self) -> None:
        mat = self._current_mat()
        if mat is not None and not mat.has_td:
            if self.type_code.get() == "TD":
                self.type_code.set("CM")
            self.rb_td.config(state="disabled")
        else:
            self.rb_td.config(state="normal")
        self._refresh_targets()
    def _refresh_targets(self) -> None:
        mat = self._current_mat()
        if mat is None:
            self.targets_var.set("")
            return
        typ = self.type_code.get()
        num = self.num.get().strip()
        date = self.date.get().strip()
        stem = canonical_stem(typ, num, mat.slug, date)
        trans = _transcription_dir(mat, typ) / f"{stem}.txt"
        fiche = _fiche_dir(mat, typ) / f"fiche_{stem}.md"
        lines = [f"Transcription : {trans.relative_to(ROOT)}",
                 f"Fiche         : {fiche.relative_to(ROOT)}"]
        self.targets_var.set("\n".join(lines))
    def _browse_audio(self) -> None:
        path = filedialog.askopenfilename(title="Choisir un fichier audio",
                                          filetypes=AUDIO_TYPES)
        if path:
            self.audio_path.set(path)
    def _clear_log(self) -> None:
        self.log.config(state="normal")
        self.log.delete("1.0", "end")
        self.log.config(state="disabled")
    def _append(self, text: str) -> None:
        self.log.config(state="normal")
        self.log.insert("end", text)
        self.log.see("end")
        self.log.config(state="disabled")
    def _on_run(self) -> None:
        if self._running:
            return
        mat = self._current_mat()
        if mat is None:
            messagebox.showwarning("Cartable", "Choisis une matière.")
            return
        typ = self.type_code.get()
        if typ == "TD" and not mat.has_td:
            messagebox.showwarning("Cartable", f"{mat.libelle} n'a pas de TD.")
            return
        num = self.num.get().strip()
        if not num.isdigit():
            messagebox.showwarning("Cartable", "Le n° de séance doit être un entier.")
            return
        date = self.date.get().strip()
        if not (date.isdigit() and 3 <= len(date) <= 8):
            messagebox.showwarning("Cartable", "Date attendue au format JJMM (ex. 1509).")
            return
        steps_on = (self.do_transcribe.get() or self.do_fiche.get()
                    or self.do_pub_trans.get() or self.do_pub_fiche.get())
        if not steps_on:
            messagebox.showwarning("Cartable", "Coche au moins une étape.")
            return
        stem = canonical_stem(typ, num, mat.slug, date)
        if self.do_transcribe.get():
            audio = self.audio_path.get().strip()
            if not audio or not Path(audio).is_file():
                messagebox.showwarning(
                    "Cartable", "Choisis un fichier audio existant pour la transcription.")
                return
            transcription = _transcription_dir(mat, typ) / f"{stem}.txt"
        else:
            audio = ""
            found = find_latest_transcription(mat, typ, num)
            transcription = found or (_transcription_dir(mat, typ) / f"{stem}.txt")
            stem = transcription.stem
        fiche = _fiche_dir(mat, typ) / f"fiche_{stem}.md"
        if not self.dry_run.get():
            need_trans = self.do_fiche.get() or self.do_pub_trans.get()
            if need_trans and not self.do_transcribe.get() and not transcription.is_file():
                messagebox.showwarning(
                    "Cartable",
                    f"Aucune transcription trouvée pour {typ}{num} {mat.slug}.\n"
                    "Coche « Transcrire » d'abord, ou vérifie matière/type/n°.")
                return
            if self.do_pub_fiche.get() and not self.do_fiche.get() and not fiche.is_file():
                messagebox.showwarning(
                    "Cartable",
                    f"Aucune fiche trouvée ({fiche.name}). Coche « Générer la fiche ».")
                return
        py = sys.executable
        dry = ["--dry-run"] if self.dry_run.get() else []
        cmds: list[tuple[str, list[str]]] = []
        if self.do_transcribe.get():
            cmds.append(("① Transcription", [
                py, "-u", str(SCRIPTS / "transcribe.py"), audio,
                "--matiere", mat.slug, "--type", typ,
                "--out", str(transcription)] + dry))
        if self.do_fiche.get():
            force = ["--force"] if self.force_fiche.get() else []
            cmds.append(("② Fiche", [
                py, "-u", str(SCRIPTS / "fiche.py"), str(transcription),
                "--matiere", mat.slug, "--type", typ] + force + dry))
        if self.do_pub_trans.get():
            salon = "transcript-cm" if typ == "CM" else "transcript-td"
            cmds.append(("③ Publication transcription", [
                py, "-u", str(SCRIPTS / "publish_discord.py"), str(transcription),
                "--matiere", mat.slug, "--salon", salon] + dry))
        if self.do_pub_fiche.get():
            cmds.append(("④ Publication fiche", [
                py, "-u", str(SCRIPTS / "publish_discord.py"), str(fiche),
                "--matiere", mat.slug, "--salon", "resumes"] + dry))
        self._set_running(True)
        threading.Thread(target=self._run_cmds, args=(cmds,), daemon=True).start()
    def _set_running(self, running: bool) -> None:
        self._running = running
        self.btn_run.config(state="disabled" if running else "normal",
                            text="… en cours" if running else "▶ Lancer")
    def _post(self, fn, *a) -> None:
        self.root.after(0, lambda: fn(*a))
    def _run_cmds(self, cmds: list[tuple[str, list[str]]]) -> None:
        try:
            for name, cmd in cmds:
                self._post(self._append, f"\n=== {name} ===\n")
                rc = self._stream(cmd)
                if rc != 0:
                    self._post(self._append,
                               f"\n[ARRÊT] « {name} » a échoué (code {rc}). "
                               "Étapes suivantes annulées.\n")
                    break
                self._post(self._append, f"[OK] {name} terminé.\n")
            else:
                self._post(self._append, "\n✅ Toutes les étapes sont terminées.\n")
        finally:
            self._post(self._set_running, False)
    def _stream(self, cmd: list[str]) -> int:
        creationflags = 0
        if os.name == "nt":
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            proc = subprocess.Popen(
                cmd, cwd=str(ROOT), stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                errors="replace", bufsize=1, creationflags=creationflags,
            )
        except FileNotFoundError as e:
            self._post(self._append, f"[ERR] commande introuvable : {e}\n")
            return 127
        assert proc.stdout is not None
        for line in proc.stdout:
            self._post(self._append, line)
        proc.wait()
        return proc.returncode
def main() -> int:
    root = tk.Tk()
    CartableGUI(root)
    root.mainloop()
    return 0
if __name__ == "__main__":
    raise SystemExit(main())