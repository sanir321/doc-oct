import os, sys, re
sys.path.insert(0, "backend")
from main import generate_ieee_html, generate_pdf_from_html, PROCOMM, IEMT
from PIL import Image, ImageDraw

d = "demo_out"
os.makedirs(f"{d}/images", exist_ok=True)
os.makedirs(f"{d}/out", exist_ok=True)

def mkfig(w,h,bg,txt,f):
    img = Image.new("RGB",(w,h),color=bg)
    dr = ImageDraw.Draw(img)
    for i, ln in enumerate(txt):
        dr.text((20,15+i*28),ln,fill=(255,255,255))
    img.save(f"{d}/images/{f}")

mkfig(550,320,(30,60,120),["Figure 1: System Architecture","Data -> Preprocessing -> Feature Extractor","-> Classification Engine -> Output","Three-tier pipeline"],"fig1_arch.jpeg")
mkfig(550,350,(20,100,40),["Figure 2: Experimental Results","Method        Accuracy","SVM           88.2%","CNN           93.8%","Transformer   95.1%","Ours          97.3%"],"fig2_results.jpeg")
mkfig(450,280,(140,50,30),["Figure 3: Confusion Matrix","Actual Pos -> Pred: 912/18","Actual Neg -> Pred: 22/848","Accuracy: 97.3%"],"fig3_matrix.jpeg")

sections = [
    {"title":"1. Introduction","content":"Machine learning has revolutionized classification tasks across various domains. Recent advances in deep learning have led to significant improvements in accuracy and efficiency, particularly through the use of transformer architectures and attention mechanisms. However, existing approaches still face challenges in handling complex, high-dimensional data with imbalanced class distributions. In this paper we propose a novel hybrid architecture that addresses these limitations through an innovative three-stage pipeline combining convolutional feature extraction with attention-based classification. Our method achieves state-of-the-art results on standard benchmarks, outperforming existing methods by a significant margin."},
    {"title":"2. System Architecture","content":"Our proposed system adopts a three-tier architecture for efficient classification. The first tier handles data ingestion and preprocessing. The second tier performs feature extraction using a novel attention mechanism. The third tier implements the classification engine.\n\n![System Architecture Overview](fig1_arch.jpeg)\n\nFigure 1 illustrates the complete architecture. The preprocessing module handles input normalization. Features flow through a multi-head attention layer before reaching the classification head. The architecture is designed for real-time inference, processing over 1000 samples per second. Each component is modular and independently optimized."},
    {"title":"3. Experimental Results","content":"We evaluated our approach on the standard benchmark dataset containing 1800 samples. Our method achieves 97.3% accuracy, outperforming the next best method by 2.2 percentage points.\n\n![Accuracy Comparison](fig2_results.jpeg)\n\nFigure 2 compares our method against baselines. Our architecture achieves superior performance across all metrics.\n\n![Confusion Matrix](fig3_matrix.jpeg)\n\nFigure 3 shows the confusion matrix. Low false positive and negative rates confirm robustness of our approach."},
    {"title":"4. Conclusion","content":"This paper presented a novel architecture achieving 97.3% accuracy. Future work will explore multi-modal learning and model compression for edge deployment."},
]

html = generate_ieee_html(
    title="A Novel Hybrid Architecture for Classification Using Attention Mechanisms",
    authors=[{"name":"John A. Doe","affiliation":"Stanford University","email":"john@stanford.edu"},{"name":"Jane B. Smith","affiliation":"MIT CSAIL","email":"jane@mit.edu"}],
    abstract="We present a hybrid architecture achieving 97.3% accuracy on standard benchmarks.",
    sections=sections,
    keywords=["machine learning","classification","attention","deep learning"],
    domain="Engineering", session_id="demo",
)

with open(f"{d}/out/paper.html","w",encoding="utf-8") as f:
    f.write(html)

pdf_bytes = generate_pdf_from_html(html, IEMT, session_dir=os.path.abspath(d))
with open(f"{d}/out/paper.pdf","wb") as f:
    f.write(pdf_bytes)

from pypdf import PdfReader
reader = PdfReader(f"{d}/out/paper.pdf")
with open(f"{d}/out/paper.pdf","rb") as f:
    ic = f.read().count(b'/Subtype /Image')
print(f"PDF: {len(pdf_bytes):,} bytes, {len(reader.pages)} pages, {ic} images")

import fitz
doc = fitz.open(f"{d}/out/paper.pdf")
for i, page in enumerate(doc):
    blocks = page.get_text("dict")["blocks"]
    left = right = 0
    mid = page.rect.width/2
    header_found = False
    for b in blocks:
        if b["type"]==0:
            txt="".join(s["text"] for l in b["lines"] for s in l["spans"]).strip()[:80]
            if txt and "IEMT" in txt or "36th" in txt:
                col = "R" if b["bbox"][0]>mid else "L"
                print(f"  Page{i+1}: HEADER at col={col} y={b['bbox'][1]:.0f}: '{txt}'")
                header_found = True
            if txt:
                (right if b["bbox"][0]>mid else left)[:0]
        elif b["type"]==1:
            col="R" if b["bbox"][0]>mid else "L"
            print(f"  Page{i+1}: IMAGE in {col} col y={b['bbox'][1]:.0f}-{b['bbox'][3]:.0f}")
    if not header_found:
        print(f"  Page{i+1}: NO HEADER")
doc.close()
