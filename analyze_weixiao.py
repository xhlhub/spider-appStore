import pandas as pd
import jieba
import jieba.analyse
import collections
import re

def clean_text(text):
    text = str(text)
    # Remove some non-informative characters
    text = re.sub(r'[^\w\s\u4e00-\u9fa5]', '', text)
    return text

def extract_keywords(texts, topK=20):
    full_text = " ".join([clean_text(t) for t in texts])
    # Extract keywords based on TF-IDF
    keywords = jieba.analyse.extract_tags(full_text, topK=topK, withWeight=False, allowPOS=('n', 'v', 'vn', 'a'))
    return keywords

def main():
    file_path = "output/微笑Todo-自律计划和时间打卡_1551532207_reviews.csv"
    
    try:
        df = pd.read_csv(file_path, on_bad_lines='skip')
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    print("================== 微笑Todo 评论分析 ==================\n")
    print(f"总评论数: {len(df)}")
    
    # Needs (Requests for features or improvements)
    # Typically contains "希望", "建议", "能不能", "要是", "增加"
    needs_keywords = ['希望', '建议', '能不能', '要是', '增加', '想要', '出个', '加一个', '优化', '可以']
    df['is_need'] = df['content'].apply(lambda x: any(kw in str(x) for kw in needs_keywords) or any(kw in str(title) for kw in needs_keywords for title in [df['title']]))
    
    needs_df = df[df['is_need']]
    print(f"\n[需求向评论数]: {len(needs_df)}")
    
    print("\n--- 高频需求关键词 (Top 15) ---")
    needs_texts = needs_df['title'].astype(str) + " " + needs_df['content'].astype(str)
    print(extract_keywords(needs_texts, 15))
    
    print("\n--- 典型需求原声 ---")
    for i, row in needs_df.sample(min(10, len(needs_df)), random_state=42).iterrows():
        print(f"[{row['rating']}星] {row['title']}: {str(row['content']).strip()[:100].replace(chr(10), ' ')}")
    
    # Pain points (Low rating 1-3)
    pain_df = df[df['rating'].isin([1, 2, 3])]
    print(f"\n[痛点向评论数 (1-3星)]: {len(pain_df)}")
    
    print("\n--- 高频痛点关键词 (Top 15) ---")
    pain_texts = pain_df['title'].astype(str) + " " + pain_df['content'].astype(str)
    print(extract_keywords(pain_texts, 15))
    
    print("\n--- 典型痛点原声 ---")
    for i, row in pain_df.sample(min(10, len(pain_df)), random_state=42).iterrows():
        print(f"[{row['rating']}星] {row['title']}: {str(row['content']).strip()[:100].replace(chr(10), ' ')}")

if __name__ == '__main__':
    main()
