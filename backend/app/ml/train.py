"""
Training script for Sentira AI ML models — Professional Grade.
Ensemble classifiers (LinearSVC + LogisticRegression + MultinomialNB) with
advanced preprocessing, sarcasm detection, and comprehensive training data.

Usage: python -m app.ml.train  (from backend/ directory)
"""
import os, re, json, random, warnings, datetime
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB, ComplementNB
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.ensemble import VotingClassifier

warnings.filterwarnings("ignore")

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "ml_models")
REPORTS_DIR = os.path.join(MODELS_DIR, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

# ════════════════════════════════════════════════════════════════
# TEXT PREPROCESSING
# ════════════════════════════════════════════════════════════════

CONTRACTIONS = {
    "can't": "cannot", "won't": "will not", "don't": "do not", "doesn't": "does not",
    "didn't": "did not", "isn't": "is not", "aren't": "are not", "wasn't": "was not",
    "weren't": "were not", "hasn't": "has not", "haven't": "have not", "hadn't": "had not",
    "wouldn't": "would not", "shouldn't": "should not", "couldn't": "could not",
    "mustn't": "must not", "shan't": "shall not", "it's": "it is", "i'm": "i am",
    "you're": "you are", "we're": "we are", "they're": "they are", "he's": "he is",
    "she's": "she is", "that's": "that is", "what's": "what is", "there's": "there is",
    "i've": "i have", "you've": "you have", "we've": "we have", "they've": "they have",
    "i'll": "i will", "you'll": "you will", "we'll": "we will", "they'll": "they will",
    "i'd": "i would", "you'd": "you would", "we'd": "we would", "they'd": "they would",
    "let's": "let us", "who's": "who is", "how's": "how is", "ain't": "is not",
}

EMOJI_MAP = {
    "😊": " happy ", "😃": " happy ", "😄": " happy ", "🙂": " happy ", "😁": " grinning ",
    "😍": " love ", "❤️": " love ", "💕": " love ", "👍": " good ", "👎": " bad ",
    "😡": " angry ", "😠": " angry ", "🤬": " angry ", "😤": " frustrated ",
    "😢": " sad ", "😭": " crying ", "💔": " heartbroken ", "😞": " disappointed ",
    "🔥": " excellent ", "⭐": " star ", "🌟": " star ", "💯": " perfect ",
    "🤮": " disgusting ", "💩": " terrible ", "🚀": " fast ", "🐌": " slow ",
    "😒": " annoyed ", "🙄": " sarcastic ", "😏": " sarcastic ", "👏": " applause ",
    "🤦": " facepalm ", "😑": " unamused ", "😐": " neutral ",
}

NEGATION_WORDS = {"not", "no", "never", "neither", "nobody", "nothing", "nowhere",
                  "nor", "cannot", "without", "hardly", "barely", "scarcely", "seldom"}

SARCASM_MARKERS = [
    "oh great", "oh wonderful", "oh perfect", "oh fantastic", "oh brilliant",
    "oh sure", "oh yeah right", "yeah right", "sure thing", "oh joy",
    "how wonderful", "how lovely", "how nice", "just what i needed",
    "thanks for nothing", "gee thanks",
    "new record", "what a surprise", "color me surprised",
    "slow clap",
]

# Negative context words that must co-occur with sarcasm markers
NEGATIVE_CONTEXT = {
    "crash", "crashes", "crashed", "crashing", "broke", "broken", "break", "breaking",
    "slow", "lag", "laggy", "freeze", "froze", "freezes", "freezing",
    "bug", "bugs", "buggy", "error", "errors", "fail", "fails", "failed", "failing",
    "terrible", "horrible", "awful", "worst", "bad", "worse", "useless", "unusable",
    "waste", "garbage", "trash", "disaster", "mess", "broken", "nothing",
    "waiting", "wait", "lost", "lose", "losing", "disappear", "disappeared",
    "drain", "drains", "empty", "wrong", "incorrect", "paint dry",
}


def preprocess_text(text: str) -> str:
    """Advanced text preprocessing for training and inference."""
    if not text or not text.strip():
        return ""
    t = text.lower().strip()
    # Emoji conversion
    for emoji, word in EMOJI_MAP.items():
        t = t.replace(emoji, word)
    # Contraction expansion
    for contraction, expansion in CONTRACTIONS.items():
        t = t.replace(contraction, expansion)
    # Normalize excessive punctuation
    t = re.sub(r'([!?.])\1{2,}', r'\1\1', t)
    t = re.sub(r'(.)\1{3,}', r'\1\1', t)
    # Normalize whitespace
    t = re.sub(r'\s+', ' ', t).strip()

    # Negation tagging: prefix words after negation with NEG_
    words = t.split()
    result, negate = [], False
    for w in words:
        if w in NEGATION_WORDS:
            negate = True
            result.append(w)
        elif negate and w in {".", "!", "?", ",", ";", "but", "however", "although"}:
            negate = False
            result.append(w)
        elif negate:
            result.append(f"NEG_{w}")
        else:
            result.append(w)
    t = " ".join(result)

    # Context-aware sarcasm detection: marker + negative context required
    has_marker = any(marker in t for marker in SARCASM_MARKERS)
    has_negative = any(neg in t for neg in NEGATIVE_CONTEXT)
    if has_marker and has_negative:
        t = "SARCASM_FLAG " + t
    return t


# ════════════════════════════════════════════════════════════════
# TRAINING DATA — SENTIMENT (with sarcasm/irony)
# ════════════════════════════════════════════════════════════════

SENTIMENT_DATA = {
    "positive": [
        "I absolutely love this product, it works perfectly",
        "Great customer support, they resolved my issue quickly",
        "The new feature update is amazing and very intuitive",
        "Very satisfied with the service quality",
        "Best app I have ever used, highly recommend",
        "The interface is clean and easy to navigate",
        "Excellent performance, no lag at all",
        "Really happy with the latest improvements",
        "Outstanding quality for the price",
        "The team did a wonderful job on this release",
        "Love the new design, much better than before",
        "This is exactly what I was looking for",
        "Smooth experience from start to finish",
        "The app runs flawlessly on my device",
        "Super fast delivery and great packaging",
        "Impressed by how responsive the team is",
        "The product exceeded my expectations",
        "Really appreciate the attention to detail",
        "Five stars, will definitely buy again",
        "User friendly and well designed application",
        "Perfect solution for my needs",
        "Works like a charm every single time",
        "The quality is top notch and worth every penny",
        "Amazing customer experience overall",
        "Thank you for making such a great product",
        "The speed improvements are noticeable",
        "Beautiful design and great functionality",
        "Everything works as expected, no issues",
        "The onboarding process was very smooth",
        "Really loving the dark mode feature",
        "Great value for money, totally worth it",
        "The support team went above and beyond to help",
        "Fantastic app with regular useful updates",
        "This solved all my problems, thank you",
        "Very intuitive layout and easy setup",
        "Wonderful product, my whole team loves it",
        "Quick and easy to use, saves me so much time",
        "The best upgrade I have made this year",
        "Seamless integration with other tools",
        "Happy to recommend this to my colleagues",
        "The app is very good it has every feature I want",
        "The pricing is also very good and reasonable",
        "Very impressed with the quality of this application",
        "This is a game changer for our workflow",
        "Absolutely brilliant, the developers nailed it",
        "I am blown away by how good this product is",
        "Our team productivity increased significantly since using this",
        "The features are exactly what we needed for our business",
        "Every penny well spent on this subscription",
        "The mobile app is just as good as the desktop version",
        "Setup was incredibly easy took only five minutes",
        "Customer service is world class, very responsive",
        "The dashboard is beautiful and informative",
        "I have tried many alternatives and this is by far the best",
        "No complaints at all, everything just works",
        "The dark theme is gorgeous and easy on the eyes",
        "Performance is blazing fast even with large datasets",
        "The documentation is excellent and well organized",
        "We migrated from a competitor and could not be happier",
        "The reporting features are incredibly detailed and useful",
        "My clients love the interface, very professional looking",
        "Excellent stability, never experienced a single crash",
        "The API is well designed and easy to integrate with",
        "This tool has saved our company hours of work every week",
        "The free plan is surprisingly generous with features",
        "Updates are frequent and always bring meaningful improvements",
        "The collaboration features make teamwork so much easier",
        "Best investment we have made for our small business",
        "The search functionality is powerful and accurate",
        "I recommended this to all my friends and they love it too",
        "Genuinely delighted with the quality and reliability",
        "The customer onboarding experience is phenomenal",
        "This application is incredibly well engineered",
        "Love how the product keeps getting better with every update",
        "Our entire department has switched to this and we are thriving",
        "The attention to detail in the UI is remarkable",
        "Hands down the best software purchase we have made",
        "This product makes my daily tasks genuinely enjoyable",
        "The integration capabilities are truly outstanding",
        "Exceptional product that has revolutionized our operations",
        "So glad we chose this over the competition",
    ],
    "negative": [
        "This app crashes every time I open it",
        "Terrible customer service, no one responded to my email",
        "The update broke everything, nothing works anymore",
        "Very frustrating experience with constant errors",
        "Worst purchase I have ever made",
        "The interface is confusing and hard to use",
        "Way too slow, takes forever to load",
        "I regret buying this product, total waste of money",
        "The app freezes and I lose all my data",
        "Too many bugs, this needs serious fixing",
        "Cannot believe how bad the quality is",
        "The payment system never works properly",
        "The feature I need most is completely broken",
        "Unacceptable performance issues",
        "I have been waiting weeks for a response from support",
        "The app drains my battery incredibly fast",
        "Nothing works as advertised",
        "Full of glitches and crashes constantly",
        "Very disappointed with this product",
        "The worst user experience I have ever had",
        "My data was not saved and I lost everything",
        "Overpriced for what you get",
        "The app keeps logging me out randomly",
        "Horrible interface, impossible to find anything",
        "The download failed multiple times",
        "This product is a complete disaster",
        "Server is always down, unreliable service",
        "Too many ads, makes the app unusable",
        "The search function does not work at all",
        "Customer support is completely useless",
        "I want a refund, this is unacceptable",
        "Buggy mess that should never have been released",
        "Cannot connect to the server at all",
        "The update removed features I was using daily",
        "Extremely poor quality for the price",
        "This product is getting worse with every update",
        "Laggy and unresponsive most of the time",
        "They clearly do not test before releasing",
        "Frustrated beyond belief with this app",
        "Absolute garbage, do not waste your money",
        "The app deleted all my data without warning",
        "I cannot believe they charge money for this broken product",
        "Every time I try to save my work disappears",
        "The notifications are broken and completely unreliable",
        "This is the buggiest software I have ever used",
        "My account got locked for no reason and support ignores me",
        "The latest update made everything ten times worse",
        "This app is a complete waste of storage space",
        "The sync feature destroys my files every single time",
        "I have lost count of how many times this has crashed today",
        "The user interface looks like it was designed in 2005",
        "Constant error messages make this product unusable",
        "The export feature produces garbled nonsense",
        "Three months in and still waiting for basic bug fixes",
        "The onboarding is so bad I almost gave up immediately",
        "They removed the only feature that made this app useful",
        "I switched to a competitor because this product is so bad",
        "The mobile app is an embarrassment compared to competitors",
        "Cannot upload anything without getting an error",
        "Performance has degraded to the point of being unusable",
        "The billing system charged me twice and support does not care",
        "Every feature they add breaks two existing ones",
        "Terrible quality control, feels like using a beta product",
        "The worst customer experience I have ever encountered",
        "This product should be pulled from the market immediately",
        "The team behind this clearly does not use their own product",
        "I feel scammed by this company",
        "Error after error after error, nothing works right",
        "The dashboard shows completely wrong statistics",
        "Login fails at least three times before it works",
        "This software has caused us nothing but headaches",
        "The product is fundamentally flawed and unreliable",
        "We wasted thousands of dollars on this terrible product",
        "Every interaction with this app is painful and frustrating",
        "The developers clearly have no idea what users actually need",
        "I would give zero stars if I could",
        "Completely unfit for purpose and a waste of time",
        "The reliability of this product is absolutely atrocious",
        "Our team unanimously voted to stop using this disaster",
        "The quality has declined dramatically since we started using it",
        # ── SARCASM / IRONY (should be classified as NEGATIVE) ──
        "Oh great, another crash, just what I needed today",
        "Wow the app crashed again, I am so surprised",
        "Sure I totally love waiting ten minutes for a page to load",
        "Oh wonderful, the update broke everything again, fantastic",
        "Yeah right this app is totally reliable, crashes only five times a day",
        "Oh perfect, my data disappeared again, what a wonderful feature",
        "Brilliant, the app froze during my presentation, love it",
        "Thanks for breaking the only feature that actually worked",
        "How lovely, another error message, my favorite part of the day",
        "Oh sure the performance is great if you enjoy watching paint dry",
        "Really impressed by how consistently this app crashes, such reliability",
        "What a surprise, the save button does not save, who would have guessed",
        "Congratulations on making the app even slower than before",
        "Wow a whole five minutes before it crashed, new record",
        "Just what I needed, another broken update, thanks so much",
        "Oh joy, the login failed again, what a delightful experience",
        "Totally loving how the app loses my work every single time",
        "Oh fantastic, another hour wasted on this buggy mess",
        "Great job team, you somehow made it worse than before",
        "Oh how wonderful, the export feature exported nothing at all",
        "Absolutely love the new feature where nothing works correctly",
        "Sure the support is great if you enjoy being ignored",
        "Thanks for the amazing update that deleted all my settings",
        "Really appreciate how the app drains my battery in thirty minutes",
        "The crashes are surprisingly consistent, at least something works",
        "Oh yeah the customer service is fast if you consider a week fast",
        "What an impressive app, it managed to lose all my data twice today",
        "Brilliant engineering, the app uses more RAM than a video game",
        "So glad I paid for the privilege of constant error messages",
        "Loving the new feature where the app randomly logs you out",
        "Oh definitely the best app ever if your standards are underground",
        "Wow such amazing quality, the buttons do not even click properly",
        "Thanks for the reliability, I can always count on it to crash",
        "The performance improvements are incredible, it is only slightly slower now",
        "What a masterpiece of software engineering, nothing works as intended",
    ],
    "neutral": [
        "The app works fine but nothing special",
        "It does what it is supposed to do",
        "Average experience, nothing to complain about",
        "The product is okay for the price",
        "Standard features, meets basic needs",
        "I have been using it for a while, it is alright",
        "The interface is functional but plain",
        "Not bad but not great either",
        "Some features are good, some need work",
        "Decent product with room for improvement",
        "It works but could use some polish",
        "The app serves its purpose adequately",
        "Not much to say, it is a basic tool",
        "The quality is acceptable for the cost",
        "Fairly standard product in the market",
        "Gets the job done without any frills",
        "The service is okay, nothing extraordinary",
        "Mixed feelings about this product overall",
        "It is a passable option if you need something quick",
        "The product has both pros and cons",
        "I do not have strong opinions about it",
        "It is a middle of the road experience",
        "Works as described in the listing",
        "The product is stable but lacks innovation",
        "No major issues but no standout features",
        "Adequate for everyday use",
        "The updates are incremental but acceptable",
        "It is fine but I might look for alternatives",
        "Satisfactory but I expected a bit more",
        "The product is unremarkable but functional",
        "I would give it a 3 out of 5",
        "Standard quality, nothing more nothing less",
        "The experience was neither good nor bad",
        "It is an average product in its category",
        "Could be better but it is not terrible",
        "Just a regular app with basic features",
        "Meets minimum expectations",
        "The product is passable for casual use",
        "It has potential but needs improvements",
        "Not the best but certainly not the worst",
        "The product does its job and that is about it",
        "I use it because I have to not because I love it",
        "It is an adequate solution for what we need right now",
        "The features are basic but they work well enough",
        "Nothing exciting but nothing broken either",
        "The pricing is fair for what you get",
        "I have used better alternatives but this is okay",
        "The performance is acceptable on most days",
        "It handles basic tasks without any problems",
        "The app has a learning curve but it is manageable",
        "Some days it works great other days it is slow",
        "I probably would not switch away but would not recommend either",
        "The updates do not seem to add much value",
        "It is a perfectly mediocre product in every way",
        "The interface is clean but lacks personality",
        "Functional enough for daily use",
        "The customer support is average",
        "I neither love nor hate this product",
        "It serves its purpose and nothing more",
        "The quality is consistent but unexceptional",
        "A reasonable choice if you do not need anything fancy",
        "I can take it or leave it honestly",
        "The app is competent but uninspiring",
        "There are pros and cons that balance each other out",
        "It is what you would expect for this price point",
        "Not terrible but there is definitely room for improvement",
        "The basics are covered but advanced features are lacking",
        "I would rate it as middle of the pack",
        "Runs fine on my device without any major hiccups",
        "It is a solid three star product",
        "The product fulfills its basic promise and nothing more",
        "Neither impressive nor disappointing honestly",
        "I have no strong feelings about this product one way or another",
        "It is a bog standard offering in this space",
        "The product works as expected but does not inspire loyalty",
        "Fairly typical for what you pay at this price tier",
        "I am ambivalent about continuing my subscription",
        "The user experience is fine but unremarkable",
        "Does what it says on the tin no more no less",
        "A perfectly adequate tool for simple tasks",
    ],
}

# ════════════════════════════════════════════════════════════════
# TRAINING DATA — CATEGORY
# ════════════════════════════════════════════════════════════════

CATEGORY_DATA = {
    "UI/UX": [
        "The interface is really confusing and hard to navigate",
        "Love the new design, looks very modern and clean",
        "The buttons are too small to tap on mobile",
        "The color scheme is terrible, hard to read text",
        "Navigation is very intuitive and well organized",
        "The layout is cluttered with too many elements",
        "Beautiful visual design, very aesthetic",
        "Dark mode is not working properly",
        "The font size is too small to read comfortably",
        "The user interface needs a complete overhaul",
        "Great use of whitespace in the new design",
        "Icons are misleading, I keep clicking the wrong thing",
        "The menu structure makes no sense at all",
        "Responsive design works perfectly on all my devices",
        "The design looks outdated compared to competitors",
        "Drag and drop feature is smooth and intuitive",
        "The animations are too slow and distracting",
        "I cannot find the settings page anywhere",
        "The search bar should be more prominent",
        "The onboarding tutorial was very helpful",
        "Accessibility features are lacking, need better contrast",
        "The dashboard layout is well thought out",
        "Too many pop-ups and modal dialogs",
        "The form fields are not clearly labeled",
        "Main page takes too long to render visually",
        "The sidebar navigation is very confusing to new users",
        "The mobile layout breaks on smaller screens",
        "I love how the design adapts to different screen sizes",
        "The dropdown menus are hard to click on touch devices",
        "The loading skeleton screens look very professional",
        "Why is the logout button hidden behind three menus",
        "The card layout makes information easy to scan quickly",
        "Too many fonts used on one page looks inconsistent",
        "The error messages are not clear enough for regular users",
        "The progress bar design is very sleek and informative",
        "Tab navigation between form fields is broken",
        "The notification badge positioning is off on mobile",
        "Color contrast between text and background fails accessibility",
        "The hover effects give nice feedback on interactive elements",
        "Page layout shifts when images load which is annoying",
        "The wizard style onboarding makes setup so much easier",
        "The breadcrumb navigation helps users not get lost",
        "Input validation messages should appear next to the field",
        "Scrollbar design clashes with the overall theme",
        "The empty state illustrations are a nice touch",
        "The visual hierarchy of the page is completely wrong",
        "Typography choices are poor and reduce readability",
        "The color palette is jarring and unprofessional",
        "Screen transitions feel janky and unpolished",
        "The UI feels dated compared to modern web apps",
    ],
    "Bugs": [
        "The app crashes every time I try to upload a file",
        "There is a bug in the login screen, it freezes",
        "The notification system is completely broken",
        "Data is not saving properly, I keep losing my work",
        "The search function returns wrong results",
        "Calendar view shows incorrect dates",
        "The export function generates corrupted files",
        "Clicking the submit button does nothing",
        "The app shows error 500 when I try to save",
        "Images are not loading in the gallery view",
        "The checkout process fails at the payment step",
        "Links in emails are broken and lead to error pages",
        "Profile picture upload causes the app to crash",
        "The filter option does not work as expected",
        "There is a memory leak causing the app to slow down",
        "Push notifications are being sent duplicate",
        "The undo function reverses the wrong action",
        "Data sync between devices is failing",
        "The progress bar shows wrong percentage",
        "Video playback stops randomly in the middle",
        "The share button sends the wrong link",
        "Copy paste is broken in the text editor",
        "Charts display wrong data after refresh",
        "Auto-save feature keeps corrupting my documents",
        "The API returns null values randomly",
        "The date picker selects the wrong date on click",
        "Pagination shows duplicate items on page two",
        "The file rename feature corrupts the file extension",
        "Sorting by price shows items in random order",
        "The favorites list keeps resetting after app restart",
        "Two factor authentication code never arrives",
        "The comment section shows replies under wrong comments",
        "Deleting one item removes a different item from the list",
        "The back button takes you to a completely wrong page",
        "Drag and drop reorders items incorrectly",
        "The form submits empty data even when fields are filled",
        "Password reset emails contain expired links",
        "The app shows yesterday date as today",
        "Uploaded images appear rotated ninety degrees",
        "The dark mode toggle does not persist between sessions",
        "Notification count badge shows wrong number",
        "Search autocomplete suggestions are completely irrelevant",
        "The print preview shows a blank page",
        "Currency conversion calculator gives wrong amounts",
        "Session timeout happens after just two minutes of inactivity",
        "The app throws a null pointer exception when loading profile",
        "Sorting breaks when there are more than one hundred items",
        "Double clicking the submit button creates duplicate entries",
        "File downloads produce zero byte corrupted files",
        "The autocomplete dropdown covers the submit button",
    ],
    "Performance": [
        "The app is extremely slow to load",
        "Page transitions take forever",
        "The application freezes when processing large files",
        "Loading times have increased significantly after the update",
        "The database queries are incredibly slow",
        "The app uses too much memory on my device",
        "Scrolling is laggy especially with large lists",
        "Server response time is unacceptably slow",
        "The search takes too long to return results",
        "The app heats up my phone when running",
        "File uploads take way too long even for small files",
        "Real-time updates are delayed by several seconds",
        "The application becomes unresponsive during peak hours",
        "Rendering time for charts is very slow",
        "The download speed through the app is terrible",
        "CPU usage spikes when opening the dashboard",
        "The initial startup time is way too long",
        "API calls are timing out frequently",
        "The video streaming quality keeps dropping",
        "The cache system seems inefficient",
        "Page refresh takes over ten seconds",
        "The analytics module is painfully slow",
        "Mobile app performance is much worse than desktop",
        "Large datasets cause the whole system to hang",
        "Response time has degraded over the past month",
        "The app takes over thirty seconds to open on my device",
        "Image loading is extremely slow even on fast wifi",
        "The notification service causes constant battery drain",
        "Animations stutter badly on mid range phones",
        "The database connection times out under heavy load",
        "Memory usage climbs steadily and never goes down",
        "The map view struggles to render more than fifty pins",
        "Report generation takes five minutes for basic queries",
        "The app consumes over one gigabyte of RAM when idle",
        "Tab switching is noticeably slower than last version",
        "The infinite scroll feature causes major lag after loading",
        "Cold start performance is terrible on older hardware",
        "Background sync drains battery twenty percent per hour",
        "The PDF export takes unreasonably long for short documents",
        "Server latency spikes during business hours",
        "The image compression is too slow for batch processing",
        "JavaScript bundle size is way too large",
        "The live preview feature causes the editor to freeze",
        "Network requests are not being batched efficiently",
        "Garbage collection pauses cause visible frame drops",
        "The time to first meaningful paint is over five seconds",
        "Queries that used to take milliseconds now take seconds",
        "The app becomes a memory hog after a few hours of use",
        "Rendering large tables causes the browser to freeze",
        "The API response times are three times slower than last month",
    ],
    "Pricing": [
        "The subscription is way too expensive for what you get",
        "Great value for money at this price point",
        "The free tier is too limited to be useful",
        "Hidden fees in the checkout process are frustrating",
        "The pricing model is confusing with too many tiers",
        "Would love a student discount option",
        "The annual plan saves a lot compared to monthly",
        "I feel overcharged for the basic features",
        "The pricing is fair compared to competitors",
        "The premium plan is not worth the extra cost",
        "Family plan pricing is very reasonable",
        "The upgrade cost is not justified by the features",
        "Billing issues keep charging me the wrong amount",
        "The refund policy is unclear and hard to find",
        "I wish there was a pay per use option",
        "The enterprise pricing is out of budget",
        "Good that there is a free trial before committing",
        "Price increase without any new features is unfair",
        "The cost benefit ratio is excellent",
        "Would appreciate more flexible pricing options",
        "The transaction fees are too high",
        "Monthly cost adds up quickly for a team",
        "Pricing page is transparent which I appreciate",
        "Cancellation fees are unreasonable",
        "Competitor offers more features at lower price",
        "The startup plan is very affordable for new businesses",
        "Why did the price go up without any announcement",
        "Paying per user is too expensive for large organizations",
        "The nonprofit discount is very generous",
        "I canceled because the price hike was not justified",
        "The pricing is confusing I do not know which plan I need",
        "Great that they offer a money back guarantee",
        "The professional plan is worth every dollar",
        "Auto renewal charged me after I thought I canceled",
        "Volume discounts would make this much more appealing",
        "The basic plan is missing critical features forcing upgrade",
        "I appreciate that pricing is shown upfront with no surprises",
        "The education discount makes this accessible for schools",
        "Why is the same feature free on competitors but paid here",
        "The lifetime deal was an amazing opportunity",
        "They nickel and dime you for every little add on feature",
        "Billing cycle options are very flexible which is nice",
        "The conversion from free to paid was seamless",
        "I wish they would offer quarterly payment options",
        "The referral discount program is very rewarding",
        "The cost of the premium plan doubled without justification",
        "We had to downgrade because the new pricing was absurd",
        "The per seat pricing makes this prohibitive for our team",
        "The free trial converted me into a paying customer easily",
        "The ROI on this product easily justifies the subscription cost",
    ],
    "Support": [
        "Customer support response time is very slow",
        "The support team was extremely helpful and polite",
        "I have been waiting days for a reply to my ticket",
        "The live chat feature is excellent for quick help",
        "No phone support available which is disappointing",
        "The help documentation is outdated and unhelpful",
        "Support agent resolved my issue in minutes",
        "The chatbot gives generic unhelpful responses",
        "Support hours are too limited for international users",
        "The knowledge base articles are well written",
        "I keep getting transferred between different agents",
        "Email support never responds to my queries",
        "The FAQ section answers most common questions",
        "Support tier for free users is basically nonexistent",
        "The community forum is very active and helpful",
        "Technical support lacks the skills to help",
        "Response time has improved significantly recently",
        "The support ticket system is hard to use",
        "Great that support is available on weekends",
        "The troubleshooting guide was very useful",
        "I had to explain my issue multiple times to different agents",
        "The callback feature for support is convenient",
        "Support documentation needs more examples",
        "The self-service portal saves a lot of time",
        "Wish there was a dedicated account manager",
        "The live agent was incredibly patient and knowledgeable",
        "I got a response within fifteen minutes impressive",
        "Support told me to clear my cache that did not help at all",
        "The video tutorials are more helpful than text documentation",
        "I submitted a ticket two weeks ago still no reply",
        "The in-app help center is well organized and searchable",
        "Support agent barely understood my problem",
        "The emergency support line saved our business yesterday",
        "They have a great onboarding specialist team",
        "Generic copy paste responses make me feel unheard",
        "The support team followed up to make sure my issue was resolved",
        "I wish support was available in more languages",
        "The automated troubleshooter actually fixed my problem",
        "Priority support for enterprise customers is worth the premium",
        "The help articles are clearly written by people who know the product",
        "Being put on hold for forty five minutes is not acceptable",
        "The support team proactively reached out about a known issue",
        "Chat support disconnected in the middle of my conversation",
        "The support portal keeps logging me out when I try to submit",
        "Support escalation process is transparent and efficient",
        "The support agents need better training on technical issues",
        "After three escalations my problem is still not solved",
        "The help desk software they use is slow and clunky itself",
        "Support was available around the clock during our migration",
        "The support team went out of their way to make things right",
    ],
    "Features": [
        "I really wish there was an offline mode",
        "The new collaboration feature is exactly what we needed",
        "Please add multi-language support",
        "The export to PDF feature is very useful",
        "Would love integration with Slack and Teams",
        "The API documentation is incomplete for developers",
        "Two factor authentication should be mandatory",
        "The reporting feature needs more customization",
        "Data visualization options are very limited",
        "Calendar integration would make this app perfect",
        "Batch processing feature saves so much time",
        "Need ability to set custom roles and permissions",
        "The mobile app is missing key features from desktop",
        "Would appreciate a plugin or extension system",
        "The import function only supports CSV not Excel",
        "Need better version control for documents",
        "The notification preferences are too limited",
        "Automation features are powerful and well implemented",
        "Need support for more file formats",
        "The template library needs more options",
        "Would love keyboard shortcuts for power users",
        "The workflow builder is a game changer feature",
        "Missing bulk edit capability for large datasets",
        "The email integration needs improvement",
        "SSO support would be great for enterprise users",
        "We desperately need a recurring task scheduler",
        "The tagging system is too basic for our workflow",
        "Please add the ability to create custom dashboards",
        "Version history for documents would be extremely useful",
        "The search needs advanced filtering and boolean operators",
        "Need the ability to create and share custom report templates",
        "An audit log feature would help with compliance requirements",
        "Multi-workspace support would help separate projects",
        "The commenting system needs threading and mentions",
        "Would love to see a Gantt chart view for projects",
        "The API rate limits are too restrictive for our use case",
        "Need better webhook support for automation workflows",
        "The file preview feature should support more formats",
        "Role based access control needs more granular permissions",
        "Dark mode should apply to exported documents too",
        "A built in screen recording feature would be very helpful",
        "Need the option to schedule reports for automatic delivery",
        "The data import wizard should support JSON and XML too",
        "Would love conditional formatting in the data grid view",
        "An integration marketplace would add tremendous value",
        "We need a proper audit trail for compliance purposes",
        "The API could really use batch operation endpoints",
        "Real time collaboration on shared documents is a must have",
        "The mobile app needs offline caching for field workers",
        "Please add support for custom fields on all record types",
    ],
}

# ════════════════════════════════════════════════════════════════
# TRAINING DATA — URGENCY
# ════════════════════════════════════════════════════════════════

URGENCY_DATA = {
    "critical": [
        "URGENT the entire system is down and no one can work",
        "We are losing money every minute this is not fixed",
        "Security breach detected, customer data may be exposed",
        "The payment system is broken customers cannot pay",
        "Production server crashed and will not restart",
        "All user accounts are locked out immediately",
        "Data loss occurring right now need emergency fix",
        "This is a showstopper bug blocking our entire team",
        "Critical vulnerability found in authentication",
        "Compliance deadline tomorrow and export is broken",
        "System is completely unusable since the last update",
        "Client threatening to cancel their enterprise contract",
        "Personal data leaking through API endpoint",
        "The database is corrupted and backups are failing",
        "Our entire business is halted because of this issue",
        "Regulatory audit in 24 hours and reports are broken",
        "Zero day security flaw found in the login system",
        "All transactions are failing, revenue loss is massive",
        "Complete service outage affecting all customers",
        "ASAP fix needed, this is destroying our reputation",
        "The production database just got wiped somehow",
        "Ransomware detected on our deployment server HELP",
        "All customer credit card data may have been compromised",
        "The application is redirecting users to a phishing site",
        "Primary and backup servers are both completely down",
        "We cannot process any orders the entire pipeline is broken",
        "Data breach notification needs to go out immediately",
        "The SSL certificate expired and all traffic is unencrypted",
        "Mission critical workflow has completely stopped working",
        "CEO is demanding an immediate fix to this critical outage",
        "Healthcare patient data is exposed through a public endpoint",
        "The payment gateway is charging customers double amounts",
        "Our SLA guarantees are being violated right now",
        "The system is sending customer data to wrong accounts",
        "Emergency this needs to be fixed in the next hour",
    ],
    "high": [
        "This bug is affecting a lot of our customers",
        "The feature we depend on is not working properly",
        "Multiple users reporting the same crash consistently",
        "We need this fixed by end of week at the latest",
        "This issue is causing significant customer complaints",
        "Major functionality is broken in the latest release",
        "Our team productivity has dropped significantly",
        "Important client presentation tomorrow and demo is broken",
        "Performance degradation is impacting user experience",
        "The workaround is not sustainable for much longer",
        "This is a high priority issue for our department",
        "Customers are starting to leave because of this",
        "The integration with our key partner is failing",
        "Sales team cannot generate quotes properly",
        "Reporting dashboard showing incorrect financial data",
        "The mobile app is unusable for most users",
        "This needs urgent attention from the development team",
        "We have escalated this issue to management",
        "Client SLA is being violated because of this",
        "The automated workflows have stopped working",
        "The app keeps crashing for all users on the latest version",
        "Checkout is completely broken customers cannot complete orders",
        "Data corruption is happening when users try to save",
        "All scheduled reports have stopped sending this morning",
        "Login functionality is broken for half our user base",
        "The API is returning errors for every single request",
        "File uploads are failing and users are losing their data",
        "The app crashes every time you try to open it",
        "Critical feature is completely non functional after update",
        "Users cannot access their accounts at all",
        "This is blocking our go live date which is next week",
        "Customers are publicly complaining on social media about this",
        "The billing system is not sending invoices to clients",
        "Our largest client has reported this bug three times now",
        "Performance has dropped fifty percent since the last deploy",
        "The onboarding flow is broken new signups cannot continue",
        "Multiple departments are affected by this issue",
        "We are getting escalation calls from unhappy customers daily",
        "The data export feature we rely on for compliance is broken",
        "Our analytics tracking has been wrong for the past week",
        "The core search functionality is returning empty results",
        "This needs to be addressed before the product launch",
        "Support tickets from this issue have doubled this week",
        "The authentication system is intermittently locking out users",
        "Report generation is failing for all enterprise accounts",
    ],
    "medium": [
        "This is somewhat annoying but I can work around it",
        "It would be nice to get this fixed in the next update",
        "Not critical but definitely impacts my workflow",
        "Minor inconvenience that happens occasionally",
        "The issue is noticeable but not a blocker",
        "Would appreciate attention to this when possible",
        "Some users have mentioned this problem",
        "It is a moderate issue that needs eventual attention",
        "This affects a subset of our user base",
        "The current workaround is acceptable for now",
        "Should be addressed in the next release cycle",
        "Intermittent issue that occurs under specific conditions",
        "Not urgent but would improve the experience",
        "A few customers have reported this over the past week",
        "Would be great to see this fixed soon",
        "The functionality works but not exactly as expected",
        "Adds extra steps to complete a simple task",
        "Impacts efficiency but does not prevent work",
        "Could become a bigger problem if left unaddressed",
        "Worth looking into during the next sprint",
        "The app sometimes crashes when uploading large files",
        "Export feature occasionally generates wrong format",
        "Some pages take a bit too long to load",
        "The filter does not always show correct results",
        "Notifications are delayed by a few minutes sometimes",
        "The app is a bit slow on older devices",
        "Search results are not always accurate",
        "The settings page has a small bug that is annoying",
        "Performance could be better on mobile browsers",
        "Charts sometimes show stale data until you refresh",
        "This problem happens about once a day for our team",
        "The workaround takes an extra five minutes each time",
        "It is not causing data loss but it is definitely inconvenient",
        "Some of our users are frustrated but most are unaffected",
        "This should probably be fixed before the next major release",
        "The issue is reproducible but only under certain conditions",
        "It is manageable for now but should be on the roadmap",
        "A handful of customers have mentioned this in their reviews",
        "The formatting breaks in certain edge cases",
        "The sorting is incorrect when special characters are used",
        "Mobile users experience this more frequently than desktop",
        "It is a known limitation that we have been working around",
        "This causes confusion but does not actually break anything",
        "We can live with this temporarily but it needs fixing",
        "The error handling for this case could be much better",
    ],
    "low": [
        "Just a minor cosmetic issue, not a big deal",
        "Small typo on the settings page",
        "Barely noticeable issue that most users would not see",
        "A nice to have improvement for the future",
        "Very minor edge case that rarely occurs",
        "Low priority suggestion for the next version",
        "The icon color is slightly off from the brand guide",
        "Would be nice to have but not important at all",
        "Tiny alignment issue on one specific page",
        "Negligible impact on overall experience",
        "Encountered it once and could not reproduce",
        "Just a small polish thing when you get around to it",
        "Minor inconsistency in the tooltip text",
        "Text wrapping looks a bit odd on very wide screens",
        "Suggestion for a future enhancement",
        "The loading spinner is a bit plain, consider improving",
        "Would be cool to add a keyboard shortcut for this",
        "Minor grammatical error in the notification email",
        "Barely affects my usage of the product",
        "A small refinement that could improve things slightly",
        "I absolutely love this product it works perfectly",
        "Great customer support they resolved my issue quickly",
        "The new feature update is amazing and very intuitive",
        "Very satisfied with the service quality overall",
        "Best app I have ever used highly recommend it",
        "The interface is clean and easy to navigate",
        "Excellent performance no lag at all",
        "Really happy with the latest improvements",
        "Outstanding quality for the price",
        "Love the new design much better than before",
        "The app is very good it has every feature I want",
        "The pricing is also very good and reasonable",
        "Great value for money totally worth it",
        "Wonderful product my whole team loves it",
        "Happy to recommend this to my colleagues",
        "Everything works as expected no issues at all",
        "Smooth experience from start to finish",
        "The product exceeded my expectations completely",
        "Five stars will definitely buy again",
        "Perfect solution for my needs thank you",
        "The app works fine but nothing special",
        "It does what it is supposed to do",
        "Average experience nothing to complain about",
        "The product is okay for the price",
        "Standard features meets basic needs",
        "Not bad but not great either",
        "Some features are good some need work",
        "Decent product with room for improvement",
        "It works but could use some polish",
        "No major issues but no standout features",
        "The border radius on one button looks a pixel off",
        "The favicon is blurry on high resolution displays",
        "One placeholder text still shows lorem ipsum",
        "The about page has an outdated copyright year",
        "The color of the link text is slightly different shade",
        "A tooltip appears a bit too slowly on hover",
        "The spacing between footer links is a bit uneven",
        "There is a brief flicker when switching dark to light mode",
        "The app is brilliant and I am so glad I found it",
        "Truly exceptional product that has transformed our workflow",
        "We are very pleased with our purchase and will renew",
        "The team behind this product clearly cares about quality",
        "I have nothing but praise for this excellent service",
        "An absolute pleasure to use every single day",
        "This product delivers on every promise they make",
    ],
}


# ════════════════════════════════════════════════════════════════
# DATA AUGMENTATION
# ════════════════════════════════════════════════════════════════

SYNONYM_DICT = {
    "good": ["great", "excellent", "wonderful", "fantastic"],
    "bad": ["terrible", "awful", "horrible", "dreadful"],
    "slow": ["sluggish", "laggy", "unresponsive", "crawling"],
    "fast": ["quick", "speedy", "rapid", "swift"],
    "broken": ["busted", "defective", "malfunctioning", "faulty"],
    "crash": ["freeze", "hang", "fail", "break"],
    "love": ["adore", "enjoy", "appreciate", "cherish"],
    "hate": ["despise", "detest", "loathe", "cannot stand"],
    "expensive": ["costly", "overpriced", "pricey", "steep"],
    "cheap": ["affordable", "inexpensive", "budget friendly", "economical"],
    "easy": ["simple", "straightforward", "effortless", "intuitive"],
    "hard": ["difficult", "complicated", "confusing", "challenging"],
    "beautiful": ["stunning", "gorgeous", "elegant", "sleek"],
    "ugly": ["hideous", "unattractive", "unappealing", "unsightly"],
    "helpful": ["useful", "valuable", "beneficial", "supportive"],
    "useless": ["worthless", "pointless", "unhelpful", "futile"],
    "amazing": ["incredible", "outstanding", "phenomenal", "remarkable"],
    "terrible": ["awful", "dreadful", "atrocious", "abysmal"],
}


def augment_text(text: str) -> str:
    """Advanced data augmentation with multiple strategies."""
    strategy = random.choice([
        "original", "lowercase", "prefix", "suffix", "synonym",
        "word_dropout", "swap_adj", "negate_prefix", "formalize", "casual",
    ])
    if strategy == "original":
        return text
    if strategy == "lowercase":
        return text.lower()
    if strategy == "prefix":
        prefix = random.choice([
            "I think ", "Honestly, ", "To be honest, ", "In my experience, ",
            "Just wanted to say: ", "FYI ", "As a long time user, ",
            "From my perspective, ", "After using this for months, ",
            "I have to say, ", "Frankly, ",
        ])
        return prefix + text[0].lower() + text[1:] if text else text
    if strategy == "suffix":
        suffix = random.choice([
            " This is really important to me.", " Can someone look into this?",
            " Please help.", " Thanks.", " ASAP.", " Please fix this.",
            " I need a solution.", " Any updates on this?",
            " This needs to be addressed.", " Hoping for a quick fix.",
        ])
        return text + suffix
    if strategy == "synonym":
        words = text.split()
        for i, w in enumerate(words):
            wl = w.lower().strip(".,!?;:")
            if wl in SYNONYM_DICT and random.random() > 0.5:
                words[i] = random.choice(SYNONYM_DICT[wl])
                break
        return " ".join(words)
    if strategy == "word_dropout":
        words = text.split()
        if len(words) > 4:
            keep = [w for w in words if random.random() > 0.15]
            return " ".join(keep) if len(keep) > 2 else text
        return text
    if strategy == "swap_adj":
        words = text.split()
        if len(words) > 3:
            i = random.randint(0, len(words) - 2)
            words[i], words[i + 1] = words[i + 1], words[i]
        return " ".join(words)
    if strategy == "negate_prefix":
        return text.replace(".", "!") if random.random() > 0.5 else text
    if strategy == "formalize":
        return text.replace("!", ".").replace("!!", ".")
    if strategy == "casual":
        return text.replace(",", "").replace(";", "")
    return text


# ════════════════════════════════════════════════════════════════
# TRAINING DATA GENERATION
# ════════════════════════════════════════════════════════════════

def generate_training_data():
    """Generate preprocessed and augmented training data."""
    random.seed(42)
    AUG_FACTOR = 6

    def expand(data_dict, aug_factor=AUG_FACTOR):
        texts, labels = [], []
        for label, samples in data_dict.items():
            for text in samples:
                processed = preprocess_text(text)
                texts.append(processed)
                labels.append(label)
                for _ in range(aug_factor):
                    augmented = augment_text(text)
                    texts.append(preprocess_text(augmented))
                    labels.append(label)
        return texts, labels

    s_texts, s_labels = expand(SENTIMENT_DATA)
    c_texts, c_labels = expand(CATEGORY_DATA)
    u_texts, u_labels = expand(URGENCY_DATA)

    return (s_texts, s_labels), (c_texts, c_labels), (u_texts, u_labels)


# ════════════════════════════════════════════════════════════════
# MODEL TRAINING — ENSEMBLE VOTING CLASSIFIER
# ════════════════════════════════════════════════════════════════

def build_feature_extractor():
    """Build a FeatureUnion combining word-level and character-level TF-IDF."""
    return FeatureUnion([
        ("word_tfidf", TfidfVectorizer(
            analyzer="word",
            max_features=15000,
            ngram_range=(1, 3),
            stop_words="english",
            sublinear_tf=True,
            min_df=2,
            max_df=0.92,
        )),
        ("char_tfidf", TfidfVectorizer(
            analyzer="char_wb",
            max_features=10000,
            ngram_range=(3, 5),
            sublinear_tf=True,
            min_df=2,
            max_df=0.92,
        )),
    ])


def train_model(texts, labels, model_name):
    """Train an ensemble voting classifier with detailed reporting."""
    print(f"\n  Training {model_name}...")
    print(f"    Samples: {len(texts)} | Classes: {len(set(labels))}")

    # Build ensemble
    svc = CalibratedClassifierCV(LinearSVC(
        C=1.0, max_iter=10000, class_weight="balanced"
    ), cv=3)

    lr = LogisticRegression(
        C=1.0, max_iter=5000, solver="lbfgs",
        class_weight="balanced",
    )

    nb = MultinomialNB(alpha=0.05)
    cnb = ComplementNB(alpha=0.3)

    # Feature extraction
    features = build_feature_extractor()

    # Voting classifier
    ensemble = VotingClassifier(
        estimators=[
            ("svc", svc),
            ("lr", lr),
            ("nb", nb),
            ("cnb", cnb),
        ],
        voting="soft",
        weights=[3, 2, 1, 1],  # SVC and LR get higher weight
    )

    pipeline = Pipeline([
        ("features", features),
        ("clf", ensemble),
    ])

    # Cross validation
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(pipeline, texts, labels, cv=cv, scoring="accuracy")
    print(f"    CV Accuracy: {np.mean(scores):.4f} (+/- {np.std(scores):.4f})")

    # Train on full data
    pipeline.fit(texts, labels)

    # Generate classification report
    y_pred = pipeline.predict(texts)
    report = classification_report(labels, y_pred, output_dict=True)
    report_text = classification_report(labels, y_pred)
    cm = confusion_matrix(labels, y_pred, labels=pipeline.classes_)

    # Save report
    report_data = {
        "model_name": model_name,
        "cv_accuracy_mean": round(float(np.mean(scores)), 4),
        "cv_accuracy_std": round(float(np.std(scores)), 4),
        "n_samples": len(texts),
        "n_classes": len(set(labels)),
        "classes": list(pipeline.classes_),
        "classification_report": report,
        "confusion_matrix": cm.tolist(),
    }

    with open(os.path.join(REPORTS_DIR, f"{model_name}_report.json"), "w") as f:
        json.dump(report_data, f, indent=2)

    with open(os.path.join(REPORTS_DIR, f"{model_name}_report.txt"), "w") as f:
        f.write(f"{'='*60}\n{model_name.upper()} — Classification Report\n{'='*60}\n\n")
        f.write(f"CV Accuracy: {np.mean(scores):.4f} (+/- {np.std(scores):.4f})\n")
        f.write(f"Samples: {len(texts)} | Classes: {len(set(labels))}\n\n")
        f.write(report_text)
        f.write(f"\nConfusion Matrix:\n{cm}\n")

    # Save model
    model_path = os.path.join(MODELS_DIR, f"{model_name}.joblib")
    joblib.dump(pipeline, model_path)
    print(f"    Saved: {model_path}")

    return pipeline, float(np.mean(scores)), float(np.std(scores))


# ════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("  Sentira AI — Professional Model Training")
    print("  Ensemble: LinearSVC + LogReg + NB + ComplementNB")
    print("=" * 60)

    print("\n📊 Generating training data...")
    (s_texts, s_labels), (c_texts, c_labels), (u_texts, u_labels) = generate_training_data()
    print(f"  Sentiment samples: {len(s_texts)}")
    print(f"  Category samples:  {len(c_texts)}")
    print(f"  Urgency samples:   {len(u_texts)}")
    print(f"  Total:             {len(s_texts) + len(c_texts) + len(u_texts)}")

    print("\n🔧 Training models...\n")
    results = {}
    for name, texts, labels in [
        ("sentiment_model", s_texts, s_labels),
        ("category_model", c_texts, c_labels),
        ("urgency_model", u_texts, u_labels),
    ]:
        _, mean_acc, std_acc = train_model(texts, labels, name)
        results[name] = (mean_acc, std_acc, len(texts), len(set(labels)))

    # Generate summary report
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    summary_lines = [
        "=" * 70,
        "  SENTIRA AI — PROFESSIONAL MODEL TRAINING SUMMARY",
        f"  Generated: {now}",
        "=" * 70,
        "",
        f"{'Model':<22} {'Samples':<10} {'Classes':<10} {'CV Accuracy':<20} {'Vocab'}",
        "-" * 70,
    ]
    for name, (mean_acc, std_acc, n_samples, n_classes) in results.items():
        summary_lines.append(
            f"{name:<22} {n_samples:<10} {n_classes:<10} "
            f"{mean_acc*100:.2f}% +/-{std_acc*100:.2f}%"
        )
    summary_lines += [
        "",
        "=" * 70,
        "  TECHNOLOGY STACK",
        "=" * 70,
        "  - Feature Extraction : TF-IDF (Word n-grams + Character n-grams)",
        "  - Classifiers        : LinearSVC + LogReg + MultinomialNB + ComplementNB",
        "  - Ensemble           : Soft Voting Classifier (weighted)",
        "  - Pipeline           : sklearn FeatureUnion + Pipeline",
        "  - Preprocessing      : Contraction expansion, negation tagging,",
        "                         emoji conversion, sarcasm marker detection",
        "  - Augmentation       : Synonym replacement, word dropout, word swap,",
        "                         prefix/suffix, case variation (6x factor)",
        "  - Serialization      : joblib (binary model files)",
        "  - Validation         : 5-Fold Stratified Cross-Validation",
        "",
        "  All models are self-hosted with zero external AI API dependencies.",
    ]

    summary_text = "\n".join(summary_lines)
    with open(os.path.join(REPORTS_DIR, "training_summary.txt"), "w") as f:
        f.write(summary_text)

    print(f"\n{'='*60}")
    print("✅ All models trained and saved successfully!")
    print(f"   Models directory: {MODELS_DIR}")
    print(f"   Reports directory: {REPORTS_DIR}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
