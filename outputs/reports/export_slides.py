"""PPTX → 슬라이드 JPG (PowerPoint COM Export 사용)"""
import os, sys, glob
import win32com.client as wc

pptx = os.path.abspath("outputs/reports/260421_보고_그룹장_선행Lab_BDT_현황및계획.pptx")
out_dir = os.path.abspath("outputs/reports/slides_jpg")
os.makedirs(out_dir, exist_ok=True)
for old in glob.glob(os.path.join(out_dir, "*.jpg")):
    os.remove(old)

# late-binding 에서 Visible 은 read-only, 무시하고 진행
app = wc.Dispatch("PowerPoint.Application")
pres = app.Presentations.Open(pptx, WithWindow=False)
for i, slide in enumerate(pres.Slides, 1):
    out = os.path.join(out_dir, f"slide-{i:02d}.jpg")
    slide.Export(out, "JPG", 1600, 900)
    print(f"  exported: {out}")
pres.Close()
try:
    app.Quit()
except Exception:
    pass

for j in sorted(glob.glob(os.path.join(out_dir, "*.jpg"))):
    print(j, os.path.getsize(j))
