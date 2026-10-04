from app.tools.web_reader import read_webpage
from app.agent.extractor import extract_product
def test_extractor():
    url = "https://amazon.com/HUADISK-Gen3x4-Internal-Heatsink，3D-Desktop/dp/B0FFGXYXQV/ref=sr_1_1?crid=3V67JLH7HCVIT&dib=eyJ2IjoiMSJ9.mff2EvIt3pRNSYeUmujwXF3rDc-wszh9naFRvOaXG5rWIj7My93HzDo1JffqX-Y3QDx-JxpklKZGErlgVg8-PU0VeRrivfZRQUm5F_z_moqIQciG5ZPOPMVLuEczQzJ9d22JbeHtwLvUIUoo3MjWad5hahpCWQNUM3RqXzfg5WfmsBesnpuOn2112baHcHVld-30_cVQ79adfkEFipSY_OqDQkTGeulE_uaI-cYSvC8.e-rNJjjbDTsg2vVtkWnYqKeYAZEd-8q-1fAywo3Xy6Y&dib_tag=se&keywords=huadisk&qid=1791107210&refresh=1&sprefix=huadisk%2Caps%2C499&sr=8-1"
    # ① 调用 web_reader，得到网页正文
    text = read_webpage(url)
    # ② 调用 extractor，把 text 传进去
    result = extract_product(text, url)
    print(result)
test_extractor()