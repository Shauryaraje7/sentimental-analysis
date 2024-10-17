from flask import Flask, request, jsonify
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from textblob import TextBlob

app = Flask(__name__)

# Replace with your YouTube API key
api_key = "AIzaSyBRW9BZNG3Wo92OSux-YUpFDjUtdPzPJvs"

@app.route('/analyze', methods=['POST'])
def analyze_sentiment():
    data = request.json
    search_query = data.get('query')

    if not search_query:
        return jsonify({'error': 'Query parameter is required.'}), 400

    try:
        youtube = build('youtube', 'v3', developerKey=api_key)

        # Search for videos related to the user-provided query
        search_response = youtube.search().list(
            q=search_query,
            part="id",
            type="video",
            maxResults=5
        ).execute()

        # Get video IDs from search results
        video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]

        # Fetch comments from the videos
        comments = []
        for video_id in video_ids:
            try:
                response = youtube.commentThreads().list(
                    videoId=video_id,
                    part="snippet",
                    maxResults=10
                ).execute()

                for item in response.get('items', []):
                    comment = item['snippet']['topLevelComment']['snippet'].get('textDisplay')
                    if comment:
                        comments.append(comment)
            except HttpError as e:
                print(f"An error occurred: {e}")
                continue

        # Sentiment Analysis
        positive_count = 0
        negative_count = 0
        neutral_count = 0

        for comment in comments:
            analysis = TextBlob(comment)
            polarity = analysis.sentiment.polarity

            if polarity > 0:
                positive_count += 1
            elif polarity < 0:
                negative_count += 1
            else:
                neutral_count += 1

        # Summarize the sentiments
        total_comments = positive_count + negative_count + neutral_count
        sentiment_summary = {
            'total_comments': total_comments,
            'positive': positive_count,
            'negative': negative_count,
            'neutral': neutral_count
        }

        # Impact Summary
        if positive_count > negative_count and positive_count > neutral_count:
            impact_summary = "Overall positive sentiment indicates optimism."
        elif negative_count > positive_count and negative_count > neutral_count:
            impact_summary = "Overall negative sentiment indicates widespread concern."
        else:
            impact_summary = "Mixed or neutral sentiment indicates balanced opinions."

        return jsonify({
            'comments': comments,
            'sentiment_summary': sentiment_summary,
            'impact_summary': impact_summary
        })

    except HttpError as e:
        return jsonify({'error': f'An error occurred while connecting to YouTube: {e}'}), 500

if __name__ == '__main__':
    app.run(debug=True)
