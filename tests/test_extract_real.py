from app.tools.web_reader import read_webpage
from app.agent.extractor import extract_product
url="https://www.amazon.com/gp/aw/d/B09VCXWPQG?pd_rd_plhdr=t&hsa_cr_id=0&qid=1791109952&sr=1-1-fec03104-6f11-4242-8f79-15fae2896f66&i=aps&aref=ceh7We7abX&_encoding=UTF8&_encoding=UTF8&pd_rd_i=B09VCXWPQG&ref_=sxts_sparkle_sbv&ref_=sbx_be_s_sparkle_ssd_vid&qid=&pd_rd_w=KrkJf&content-id=amzn1.sym.22e060df-ce87-467b-805a-61b8bd37fbe9%3Aamzn1.sym.22e060df-ce87-467b-805a-61b8bd37fbe9&pf_rd_p=22e060df-ce87-467b-805a-61b8bd37fbe9&pf_rd_r=CC70NG8FRXHVNESSYRVQ&pd_rd_wg=EUyAi&pd_rd_r=95681bf4-4fc9-4cbd-a904-4f826668f18f"
text=read_webpage(url)
result=extract_product(
    text,
    url
)
print(result)