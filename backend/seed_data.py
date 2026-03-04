"""
Seed script to populate the database with sample feedback for demo purposes.
Usage: python seed_data.py  (from backend/ directory, with server running)
"""
import requests
import random
import time

BASE = "http://localhost:8000/api"

SAMPLE_FEEDBACKS = [
    "I absolutely love this product, it works perfectly!",
    "The app crashes every time I try to upload a file",
    "Great customer support, resolved my issue quickly",
    "The interface is confusing and hard to navigate",
    "Very satisfied with the service quality overall",
    "Way too slow, takes forever to load anything",
    "The new feature update is amazing and intuitive",
    "URGENT the payment system is completely broken",
    "The pricing is fair compared to competitors",
    "The chatbot gives generic unhelpful responses",
    "Love the new design, much better than before",
    "Multiple users reporting the same crash issue",
    "The app serves its purpose adequately",
    "Please add multi-language support",
    "I have been waiting weeks for a support response",
    "Outstanding quality for the price, highly recommend",
    "The notification system is completely broken",
    "Best app I have ever used, five stars",
    "The subscription is way too expensive",
    "The app runs flawlessly on my device",
    "Hidden fees in the checkout are frustrating",
    "The app is extremely slow to load pages",
    "Beautiful visual design, very aesthetic overall",
    "This is a showstopper bug blocking our team",
    "Standard features, meets basic needs adequately",
    "The live chat feature works great for quick help",
    "The app freezes and I lose all my data",
    "Really happy with the latest improvements",
    "Too many bugs, this whole thing needs fixing",
    "Would love integration with Slack and Teams",
    "The mobile app is missing key desktop features",
    "The export to PDF feature is very useful",
    "Server is always down, unreliable service overall",
    "Smooth experience from start to finish",
    "Security breach detected, customer data exposed",
    "Not bad but not great either to be honest",
    "The FAQ section answers most common questions",
    "The download failed multiple times in a row",
    "Perfect solution for my workflow needs",
    "CPU usage spikes when opening the dashboard",
    "The font size is too small to read comfortably",
    "Automation features are powerful and well built",
    "We are losing money every minute this is broken",
    "It works but could use some polish overall",
    "The onboarding tutorial was very helpful",
    "All user accounts are locked out immediately",
    "Average experience, nothing to complain about",
    "Data sync between devices is failing badly",
    "The reporting feature needs more customization",
    "Really appreciate the attention to detail here",
]

def seed():
    print("🌱 Seeding sample feedback data...")
    success = 0
    for i, text in enumerate(SAMPLE_FEEDBACKS):
        try:
            res = requests.post(f"{BASE}/feedback/", json={"text": text, "source": "seed"})
            if res.status_code == 200:
                data = res.json()
                print(f"  [{i+1:2d}] {data['sentiment']:>8s} | {data['category']:<12s} | {data['urgency']:<8s} | {text[:50]}...")
                success += 1
            else:
                print(f"  [{i+1:2d}] FAILED: {res.status_code}")
        except Exception as e:
            print(f"  [{i+1:2d}] ERROR: {e}")
        time.sleep(0.05)  # Small delay to avoid overwhelming

    print(f"\n✅ Seeded {success}/{len(SAMPLE_FEEDBACKS)} feedbacks successfully!")

    # Test analytics
    print("\n📊 Testing analytics endpoint...")
    res = requests.get(f"{BASE}/analytics/overview")
    if res.status_code == 200:
        data = res.json()
        print(f"  Total: {data['total_feedbacks']}")
        print(f"  Sentiment: {data['sentiment_distribution']}")
        print(f"  Categories: {data['category_distribution']}")

    print("\n💡 Testing insights endpoint...")
    res = requests.get(f"{BASE}/analytics/insights")
    if res.status_code == 200:
        data = res.json()
        print(f"  Overall Health: {data['overall_health']}")
        print(f"  Insights Count: {len(data['insights'])}")
        for ins in data['insights']:
            print(f"    [{ins['priority']:>6s}] {ins['title']}")

    print("\n🎉 Seed complete! Open http://localhost:5173 to see the dashboard.")


if __name__ == "__main__":
    seed()
