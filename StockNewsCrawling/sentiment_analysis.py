import os
import jieba
import re
import matplotlib.pyplot as plt

# Convert results to a DataFrame
import pandas as pd

# Define the full path to the sentiment files
positive_file_path = "C:/Users/ziwei/source/GraduateProject/senior-project-main/StockNewsCrawling/ntusd-positive.txt"
negative_file_path = "C:/Users/ziwei/source/GraduateProject/senior-project-main/StockNewsCrawling/ntusd-negative.txt"


# Load and preprocess NTUSD positive and negative words
def load_sentiment_words(file_path):
    encodings = ["utf-16", "utf-8", "utf-16-le", "utf-16-be"]
    for encoding in encodings:
        try:
            with open(file_path, encoding=encoding, mode="r") as f:
                lines = f.readlines()
            words = []
            for line in lines:
                clean_words = re.findall(r"\w+", line)
                words.extend(clean_words)
            # print(f"Loaded words from {file_path} using {encoding}: {words[:20]}")
            return words
        except UnicodeError:
            print(f"Failed to decode {file_path} using {encoding}")
        except FileNotFoundError:
            print(f"Sentiment words file not found at: {file_path}")
            return []
    print(f"All encoding attempts failed for file: {file_path}")
    return []


positive_words = load_sentiment_words(positive_file_path)
negative_words = load_sentiment_words(negative_file_path)

stock_ids = ["2731"]
stock_names = ["雄獅"]
results = []

for idx, stock_id in enumerate(stock_ids):
    folderpath = os.path.join(
        os.path.dirname(os.path.abspath(os.getcwd())),
        "senior-project-main",
        "StockNewsCrawling",
        "stock_news",
        stock_id,
    )

    if not os.path.exists(folderpath):
        print(f"Directory does not exist: {folderpath}")
        continue

    sorted_news_files = sorted(os.listdir(folderpath))
    print("Sorted news files:", sorted_news_files)

    for subdir in sorted_news_files:
        subdir_path = os.path.join(folderpath, subdir)
        if os.path.isdir(subdir_path):
            subdir_files = sorted(os.listdir(subdir_path))

            for file_name in subdir_files:
                date = file_name[-8:]  # 获取文件名中的日期部分
                # 检查日期是否属于 2023 年
                if date.startswith("2023"):
                    print(f"Stock&News: {subdir}, File: {file_name}, Date: {date}")
                    file_path = os.path.join(subdir_path, file_name)

                    try:
                        with open(file_path, encoding="utf-8") as file:
                            article = file.read()
                    except Exception as e:
                        print(f"Failed to read {file_path}: {e}")
                        continue

                    # Initialize sentiment score
                    score = 0

                    # Segment text using jieba
                    jieba_result = jieba.cut(article, cut_all=False, HMM=True)

                    # Analyze sentiment
                    for word in jieba_result:
                        if word in positive_words:
                            score += 1
                        elif word in negative_words:
                            score -= 1

                    # Store the results
                    results.append((date, score))

                    print(f"檔案: {file_path}, 總分: {score}")


df = pd.DataFrame(results, columns=["Date", "Score"])
df["Date"] = pd.to_datetime(df["Date"])
df = df.sort_values(by="Date")

# Plot the results
plt.figure(figsize=(12, 5))
plt.plot(df["Date"], df["Score"], marker="o", linestyle="-")
plt.xlabel("Date")
plt.ylabel("Sentiment Score")
plt.title("Sentiment Score Over Time")
plt.grid(True)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(f"{stock_id}_sentiment_score_over_time.png")
plt.show()
