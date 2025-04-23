import pandas as pd
from time import sleep
import os
from dotenv import load_dotenv
from openpyxl import Workbook
from datetime import datetime
from openpyxl import load_workbook
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor
import random
# Load environment variables
load_dotenv()

# Set your OpenAI API key
clients = []
for i in range(1, 5):
    clients.append(OpenAI(
        api_key=os.getenv(f'open_ai_key{i}')
    ))

def get_client():
    return clients[random.randint(0, len(clients) - 1)]

def get_model():
    models = ["gpt-4o-mini", "gpt-4.1-mini", "gpt-4.1-nano", 'gpt-4o', 'gpt-3.5-turbo']
    return models[random.randint(0, len(models) - 1)]

def classify_sentiment(comment):
    while True:
        try:
            response = get_client().chat.completions.create(
                model=get_model(),
                messages=[
                    {"role": "system", "content": "You are a sentiment analyzer. Classify the following comment as 'positive', 'negative', or 'neutral'. Respond with only one word. Examples: Input: 'I love this product, it's amazing!' Output: 'positive'. Input: 'This is the worst service ever' Output: 'negative'. Input: 'The package arrived on time' Output: 'neutral'"},
                    {"role": "user", "content": comment}
                ],
                temperature=0.3
            )
            sentiment = response.choices[0].message.content.strip().lower()
            
            # Remove any quotes from the sentiment
            sentiment = sentiment.strip("'\"")
            
            if sentiment in ['positive', 'negative', 'neutral']:
                return sentiment
            else:
                print(f"Invalid sentiment received: {sentiment}. Retrying...")
                
        except Exception as e:
            if "rate limit" in str(e):
                print(f"Rate limit exceeded. Retrying in 2 seconds...")
                sleep(2)
            else:
                print(f"Error processing comment: {e}")

def process_comment(row_tuple):
    row = row_tuple[1]  # Get the row data from the tuple
    comment = row['comment_content']
    print(f"Processing comment: {comment}")
    if "شيراز" in comment or "معاذ" in comment:
        return None
    sentiment = classify_sentiment(comment)
    print(f"Sentiment: {sentiment}")
    return {
        'comment_content': comment,
        'sentiment': sentiment,
        'show_name': row['show_name']
    }

def process_comments(input_file, output_file):
    try:
        df = pd.read_csv(input_file)
        
        # Create or load existing Excel file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{output_file}_{timestamp}.xlsx"
        
        # Create a new DataFrame with only the required columns
        result_df = pd.DataFrame(columns=['comment_content', 'sentiment', 'show_name'])
        
        print("Processing comments...")
        num_comments = 0
        for i in range(0, len(df), 30):
            batch = df.iloc[i:i+30]
            with ThreadPoolExecutor(max_workers=30) as executor:
                results = list(executor.map(process_comment, batch.iterrows()))
            results = [result for result in results if result is not None]
            result_df = pd.concat([result_df, pd.DataFrame(results)], ignore_index=True)
            result_df.to_excel(output_filename, index=False)
            print(f"Progress saved to {output_filename}, progress: {i/len(df)*100}%")
            num_comments += len(results)
                
        print(f"Processed {num_comments} comments")
        print(f"Final results saved to {output_filename}")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    input_file = "comments.csv"  # Your input CSV file
    output_file = "sentiment_analysis"  # Base name for output file
    process_comments(input_file, output_file)
