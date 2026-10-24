"""Export SafeArena PowerPoint slides to high-resolution PNGs and PDF using PowerPoint COM automation.
"""
import os
import sys
from pathlib import Path
import win32com.client

deck_dir = Path(r"C:\Users\lenovo\.gemini\antigravity\scratch\SafeArena")
pptx_path = deck_dir / "SafeArena_Premium_Pitch_Deck.pptx"
pdf_path = deck_dir / "SafeArena_Premium_Pitch_Deck.pdf"
preview_dir = deck_dir / "slides_preview"
preview_dir.mkdir(parents=True, exist_ok=True)

print(f"Opening presentation: {pptx_path}")
ppt_app = win32com.client.Dispatch("PowerPoint.Application")
pres = None
try:
    pres = ppt_app.Presentations.Open(str(pptx_path.resolve()), WithWindow=False)
    print(f"Presentation opened. Total slides: {pres.Slides.Count}")

    # Export to PDF
    print(f"Exporting to PDF: {pdf_path}")
    pres.SaveAs(str(pdf_path.resolve()), 32) # 32 = ppSaveAsPDF
    print("PDF export complete.")

    # Export each slide to PNG
    for idx in range(1, pres.Slides.Count + 1):
        slide = pres.Slides(idx)
        png_name = f"slide_{idx:02d}.png"
        out_file = preview_dir / png_name
        slide.Export(str(out_file.resolve()), "PNG", 1920, 1080)
        print(f"Exported {png_name} (Size: {out_file.stat().st_size} bytes)")

    print("All slides successfully exported to PNG!")
finally:
    if pres:
        pres.Close()
    ppt_app.Quit()

print("PowerPoint COM session terminated.")
