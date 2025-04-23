import pandas as pd
from time import sleep
import os
from openpyxl import Workbook
from datetime import datetime
from openpyxl import load_workbook
from openai import OpenAI

# Set your OpenAI API key
client = OpenAI(
    api_key=os.getenv('open_ai_key')
)

def classify_sentiment(comment):
    while True:
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
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
            print(f"Error processing comment: {e}")

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
        for index, row in df.iterrows():
            comment = row['comment_content']
            if "شيراز" in comment or "معاذ" in comment:
                continue
                
            num_comments += 1
            print(f"Processing comment: {comment}")
            sentiment = classify_sentiment(comment)
            print(f"Sentiment: {sentiment}")
            
            # Add the new row to result DataFrame
            new_row = {
                'comment_content': comment,
                'sentiment': sentiment,
                'show_name': row['show_name']
            }
            result_df = pd.concat([result_df, pd.DataFrame([new_row])], ignore_index=True)
            
            # Save to Excel after each successful sentiment analysis
            result_df.to_excel(output_filename, index=False)
            print(f"Progress saved to {output_filename}")
            
            
        print(f"Processed {num_comments} comments")
        print(f"Final results saved to {output_filename}")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    input_file = "comments.csv"  # Your input CSV file
    output_file = "sentiment_analysis"  # Base name for output file
    process_comments(input_file, output_file)
