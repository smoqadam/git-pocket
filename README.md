# Read It Later - GitHub Actions

A powerful "Read It Later" tool that saves web articles to your own GitHub Pages site using GitHub Actions. Your personal reading archive powered by GitHub with advanced features like search, RSS feeds, and image handling.

[Demo](https://smoqadam.github.io/rilga/index.html)

## ✨ Features

- **📚 Article Extraction**: Clean article text with metadata (author, date, summary)
- **🔍 Full-Text Search**: JavaScript-powered search through titles, authors, and keywords
- **📱 Responsive Design**: Beautiful, mobile-friendly interface
- **🖼️ Image Handling**: Downloads and optimizes images for offline viewing
- **📡 RSS Feed**: Auto-generated RSS feed for your saved articles
- **🔄 Duplicate Detection**: Prevents saving the same article twice
- **📊 Rich Metadata**: Extracts and displays author, date, summary, and keywords
- **🎨 Modern UI**: Clean, professional design with hover effects and animations
- **📖 Reading Experience**: Optimized typography and layout for comfortable reading

## Why This Exists

GitHub is free and many developers already use it. This project turns your GitHub account into a personal read-it-later service with advanced features. No subscriptions, no third-party storage, just your own archive built with tools you already have.

## How It Works

The system uses GitHub's repository dispatch feature to trigger article extraction:

1. **You send a URL** via HTTP POST request to GitHub's API
2. **GitHub Actions triggers** and checks out your repository
3. **Article extraction** happens using Python's newspaper library
4. **Metadata is extracted** (author, date, summary, keywords)
5. **Images are downloaded** and optimized for local storage
6. **Content is saved** as a formatted HTML file with rich styling
7. **Search index is updated** with article metadata
8. **RSS feed is generated** with latest articles
9. **GitHub Pages deploys** the updated site automatically

```
URL Request → GitHub API → Actions Workflow → Extract Article → Process Images → Update Search Index → Generate RSS → Deploy
```

## Setup Instructions

### 1. Fork or Clone This Repository

```bash
git clone https://github.com/yourusername/ReadItLater-GA.git
cd ReadItLater-GA
```

### 2. Enable GitHub Pages

1. Go to your repository's **Settings** tab
2. Scroll down to **Pages** section
3. Set **Source** to "Deploy from a branch"
4. Select **gh-pages** branch and **/ (root)** folder
5. Click **Save**

### 3. Generate a Personal Access Token

1. Go to GitHub **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
2. Click **Generate new token (classic)**
3. Give it a descriptive name like "ReadItLater Dispatch"
4. Select these scopes:
   - `repo` (Full control of private repositories)
   - `workflow` (Update GitHub Action workflows)
5. Copy the generated token (you won't see it again!)

### 4. Test the Setup

Send a test request to add your first article:

```bash
curl -X POST \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: token YOUR_PERSONAL_ACCESS_TOKEN" \
  https://api.github.com/repos/YOUR_USERNAME/YOUR_REPO_NAME/dispatches \
  -d '{"event_type":"new-url","client_payload":{"url":"https://example.com/some-article"}}'
```

Replace:
- `YOUR_PERSONAL_ACCESS_TOKEN` with your token
- `YOUR_USERNAME` with your GitHub username
- `YOUR_REPO_NAME` with your repository name
- The URL with an actual article you want to save

## Usage

### Adding Articles

#### Method 1: Command Line (cURL)

```bash
curl -X POST \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: token YOUR_TOKEN" \
  https://api.github.com/repos/YOUR_USERNAME/YOUR_REPO/dispatches \
  -d '{"event_type":"new-url","client_payload":{"url":"ARTICLE_URL"}}'
```

#### Method 2: Browser Bookmarklet

Create a bookmarklet for one-click saving. Add this as a bookmark:

```javascript
javascript:(function(){var url=encodeURIComponent(window.location.href);fetch('https://api.github.com/repos/YOUR_USERNAME/YOUR_REPO/dispatches',{method:'POST',headers:{'Accept':'application/vnd.github.v3+json','Authorization':'token YOUR_TOKEN','Content-Type':'application/json'},body:JSON.stringify({event_type:'new-url',client_payload:{url:window.location.href}})}).then(r=>r.ok?alert('Article saved!'):alert('Error saving article'));})();
```

#### Method 3: Mobile Shortcut (iOS)

Create an iOS Shortcut that:
1. Gets the current webpage URL
2. Makes the HTTP request to GitHub API
3. Shows a confirmation message

### Viewing Your Archive

Once articles are processed, visit your GitHub Pages URL:
`https://YOUR_USERNAME.github.io/YOUR_REPO_NAME`

## 🎯 New Features Usage

### Search Functionality
- Use the search box on the index page to find articles by title, author, or keywords
- Press Escape to clear the search
- Real-time filtering as you type

### RSS Feed
- Access your RSS feed at `/rss.xml`
- Subscribe in your favorite RSS reader
- Contains the latest 20 articles

### Rich Metadata
- Each article displays author, publication date, and summary
- Keywords are extracted and displayed as tags
- Clean, readable layout with improved typography

### Image Handling
- Images are automatically downloaded and stored locally
- Images are optimized and resized for better performance
- All images work offline once downloaded

### Duplicate Prevention
- URLs are checked against existing articles before processing
- Prevents saving the same article multiple times
- Uses URL hashing for efficient comparison

## Project Structure

```
ReadItLater-GA/
├── .github/workflows/
│   └── publish.yaml          # GitHub Actions workflow
├── entries/                  # Generated article files
├── images/                   # Downloaded and optimized images
├── extract.py               # Enhanced extraction script
├── requirements.txt         # Python dependencies
├── index.html              # Generated index with search
├── rss.xml                 # Generated RSS feed
├── metadata.json           # Article metadata storage
└── README.md               # This file
```

## Customization

### Styling

The new design uses CSS Grid and Flexbox with:
- Gradient backgrounds
- Card-based layouts
- Smooth hover animations
- Responsive breakpoints
- Modern typography

### Search Configuration
Modify the search functionality in `extract.py`:
- Change which fields are searchable
- Adjust search sensitivity
- Add search highlighting

### RSS Feed
Customize the RSS feed generation:
- Change the number of items included
- Modify feed metadata
- Add custom categories

### Image Processing
Configure image handling:
- Change maximum image width
- Adjust compression quality
- Set different image formats

## 🔧 Advanced Configuration

### Error Handling
The system now includes comprehensive logging:
- All operations are logged with timestamps
- Errors are caught and logged appropriately
- Failed operations don't stop the entire process

### Metadata Storage
Article metadata is stored in `metadata.json`:
```json
{
  "2024-01-15-1230-example-article": {
    "title": "Example Article",
    "url": "https://example.com/article",
    "date": "2024-01-15T12:30:00",
    "authors": ["John Doe"],
    "summary": "Article summary...",
    "keywords": ["tech", "programming"]
  }
}
```

## Limitations

- **Article quality depends on the source** - Some sites may not extract cleanly
- **JavaScript-heavy sites** may not work well with the newspaper library
- **Rate limits** - GitHub API has rate limits (5000 requests/hour for authenticated users)
- **Repository size** - Large numbers of articles may impact repository size

## Troubleshooting

### Articles aren't being saved
1. Check the Actions tab for workflow errors
2. Verify your personal access token has correct permissions
3. Ensure the repository dispatch payload is correctly formatted

### Extraction fails for certain sites
- Some sites block automated access
- Try the URL in a private browser to ensure it's publicly accessible
- Check if the site requires JavaScript to load content

### GitHub Pages not updating
- Check if GitHub Pages is enabled in repository settings
- Verify the gh-pages branch exists and has content
- GitHub Pages updates may take a few minutes to propagate

### New Feature Issues

**Search not working**
- Check if JavaScript is enabled in your browser
- Verify the metadata.json file is being generated

**Images not displaying**
- Check if the images directory exists in your gh-pages branch
- Some sites may block image downloads

**RSS feed empty**
- Ensure articles have been processed and metadata exists
- Check that rss.xml is being generated in the workflow

**Duplicate articles still being saved**
- Check if the metadata.json file is being preserved between deployments
- Verify URL normalization is working correctly

## Contributing

Feel free to submit issues and enhancement requests! Some ideas for improvements:

- Better mobile interface
- Search functionality
- Tag/category system
- Export options
- Better error handling

## License

This project is open source and available under the [MIT License](LICENSE).

## 📈 Performance Features

- **Lazy Loading**: Large lists are handled efficiently
- **Image Optimization**: Images are compressed and resized
- **Caching**: Metadata is cached to prevent reprocessing
- **Efficient Search**: Client-side search with no server requests

---

**Happy Reading!** 📚✨
