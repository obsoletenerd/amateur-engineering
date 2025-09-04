#!/usr/bin/env python3
"""
RSS Feed Aggregator for Amateur Engineering Webring
Fetches RSS feeds from a GitHub-hosted JSON list and extracts post details

TODO: Build an API for posts to be saved to and read from
TODO: Modify this script to use the API to check last post-date added, and only add new ones after that date
TODO: Figure out what to do about people editing/deleting their posts
"""

import json
import requests
import feedparser
from datetime import datetime
from urllib.parse import urljoin, urlparse
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RSSAggregator:
    def __init__(self, feed_list_url, max_posts_per_feed=10):
        self.feed_list_url = feed_list_url
        self.max_posts_per_feed = max_posts_per_feed
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Amateur-Engineering-RSS-Aggregator/1.0'
        })

    def load_feed_list(self):
        """Load the list of feeds from GitHub JSON file."""
        try:
            logger.info(f"Loading feed list from: {self.feed_list_url}")
            response = self.session.get(self.feed_list_url, timeout=10)
            response.raise_for_status()

            data = response.json()
            feeds = data.get('feeds', [])
            logger.info(f"Loaded {len(feeds)} feeds from list")
            return feeds

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to load feed list: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse feed list JSON: {e}")
            raise

    def get_base_url(self, url):
        """Extract the base URL (domain) from a full URL."""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def fetch_feed(self, feed_info):
        """Fetch and parse a single RSS/Atom feed."""
        feed_name = feed_info.get('name', 'Unknown')
        feed_url = feed_info.get('url')

        if not feed_url:
            logger.warning(f"No URL provided for feed: {feed_name}")
            return []

        try:
            logger.info(f"Fetching feed: {feed_name} from {feed_url}")

            # Use feedparser which handles most RSS/Atom formats and issues
            parsed_feed = feedparser.parse(feed_url)

            if parsed_feed.bozo and parsed_feed.bozo_exception:
                logger.warning(f"Feed parsing issue for {feed_name}: {parsed_feed.bozo_exception}")

            posts = []
            entries = parsed_feed.entries[:self.max_posts_per_feed]

            for entry in entries:
                post = self.extract_post_data(entry, feed_info)
                if post:
                    posts.append(post)

            logger.info(f"Extracted {len(posts)} posts from {feed_name}")
            return posts

        except Exception as e:
            logger.error(f"Failed to fetch feed {feed_name}: {e}")
            return []

    def extract_post_data(self, entry, feed_info):
        """Extract relevant data from a feed entry."""
        try:
            # Extract post URL
            post_url = getattr(entry, 'link', '')
            if not post_url:
                return None

            # Extract title
            title = getattr(entry, 'title', '').strip()
            if not title:
                return None

            # Extract and parse date
            published_parsed = getattr(entry, 'published_parsed', None)
            updated_parsed = getattr(entry, 'updated_parsed', None)

            post_date = None
            if published_parsed:
                post_date = datetime(*published_parsed[:6])
            elif updated_parsed:
                post_date = datetime(*updated_parsed[:6])
            else:
                # Fallback to current time if no date found
                post_date = datetime.now()
                logger.warning(f"No date found for post: {title}")

            # Extract description/summary
            description = ''
            if hasattr(entry, 'summary'):
                description = entry.summary
            elif hasattr(entry, 'description'):
                description = entry.description
            elif hasattr(entry, 'content') and entry.content:
                # Handle multiple content types
                if isinstance(entry.content, list) and len(entry.content) > 0:
                    description = entry.content[0].get('value', '')
                else:
                    description = str(entry.content)

            # Clean up description (remove HTML tags, limit length)
            if description:
                import re
                description = re.sub(r'<[^>]+>', '', description)  # Strip HTML
                description = description.strip()
                if len(description) > 500:
                    description = description[:500] + '...'

            # Get author info
            author_name = feed_info.get('author', '')
            if not author_name and hasattr(entry, 'author'):
                author_name = entry.author

            # Get homepage/base URL
            homepage_url = self.get_base_url(feed_info.get('url', ''))

            # If we have a link in the feed metadata, use that instead
            if 'homepage' in feed_info:
                homepage_url = feed_info['homepage']
            elif hasattr(entry, 'link'):
                homepage_url = self.get_base_url(entry.link)

            post_data = {
                'date_posted': post_date.isoformat(),
                'date_posted_timestamp': int(post_date.timestamp()),
                'title': title,
                'url': post_url,
                'summary': description,
                'author_name': author_name,
                'author_homepage': homepage_url,
                'blog_name': feed_info.get('name', ''),
                'feed_url': feed_info.get('url', '')
            }

            return post_data

        except Exception as e:
            logger.error(f"Error extracting post data: {e}")
            return None

    def aggregate_all_feeds(self):
        """Fetch all feeds and return aggregated post data."""
        try:
            feeds = self.load_feed_list()
            all_posts = []

            for feed_info in feeds:
                posts = self.fetch_feed(feed_info)
                all_posts.extend(posts)

                # Be nice to servers - small delay between requests
                time.sleep(0.5)

            # Sort by date (newest first)
            all_posts.sort(key=lambda x: x['date_posted_timestamp'], reverse=True)

            logger.info(f"Total posts aggregated: {len(all_posts)}")
            return all_posts

        except Exception as e:
            logger.error(f"Failed to aggregate feeds: {e}")
            return []

    def save_to_json(self, posts, filename='aggregated_posts.json'):
        """Save posts to a JSON file."""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'generated_at': datetime.now().isoformat(),
                    'total_posts': len(posts),
                    'posts': posts
                }, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved {len(posts)} posts to {filename}")

        except Exception as e:
            logger.error(f"Failed to save posts to JSON: {e}")

# Put it all together
def main():
    """Main function to run the RSS aggregator."""
    feed_list_url = "https://raw.githubusercontent.com/obsoletenerd/amateur-engineering/refs/heads/main/feeds.json"

    # Initialise aggregator
    aggregator = RSSAggregator(feed_list_url)

    # Fetch all posts
    posts = aggregator.aggregate_all_feeds()

    if posts:
        # Save to JSON file (until API is sorted)
        aggregator.save_to_json(posts)

        # Display some stats
        print(f"\n=== RSS Aggregation Complete ===")
        print(f"Total posts fetched: {len(posts)}")
        print(f"Date range: {posts[-1]['date_posted']} to {posts[0]['date_posted']}")

        # Show first few posts as example
        print(f"\nLatest posts:")
        for i, post in enumerate(posts[:5]):
            print(f"  {i+1}. {post['title']} ({post['blog_name']})")

        # Here's where we would send to the API instead
        # send_to_api(posts) ... etc

    else:
        print("No posts were fetched.")


if __name__ == "__main__":
    main()
